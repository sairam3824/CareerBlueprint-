"""
Application Tracker Module
Stores and manages application data in Excel/Google Sheets/SQLite
"""

import logging
import sqlite3
import pandas as pd
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


class ExcelStorage:
    """Excel-based storage for applications"""
    
    def __init__(self, file_path: str = "./data/applications.xlsx"):
        self.file_path = Path(file_path)
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize_file()
    
    def _initialize_file(self):
        """Create Excel file with schema if it doesn't exist"""
        if not self.file_path.exists():
            df = pd.DataFrame(columns=[
                "application_id", "timestamp", "user_email", "user_name",
                "job_title", "company", "location", "salary", "job_url",
                "status", "reference_number", "skills_matched", 
                "retry_count", "last_updated"
            ])
            df.to_excel(self.file_path, index=False, engine='openpyxl')
    
    def save(self, application: Dict) -> str:
        """Save application and return application ID"""
        df = pd.read_excel(self.file_path, engine='openpyxl')
        
        # Add new row
        new_row = pd.DataFrame([application])
        df = pd.concat([df, new_row], ignore_index=True)
        
        # Save
        df.to_excel(self.file_path, index=False, engine='openpyxl')
        
        return application["application_id"]
    
    def get_by_email(self, email: str) -> List[Dict]:
        """Get all applications for a user"""
        df = pd.read_excel(self.file_path, engine='openpyxl')
        user_apps = df[df["user_email"] == email]
        return user_apps.to_dict('records')
    
    def update_status(self, application_id: str, status: str):
        """Update application status"""
        df = pd.read_excel(self.file_path, engine='openpyxl')
        df.loc[df["application_id"] == application_id, "status"] = status
        df.loc[df["application_id"] == application_id, "last_updated"] = datetime.now().isoformat()
        df.to_excel(self.file_path, index=False, engine='openpyxl')
    
    def get_all(self) -> List[Dict]:
        """Get all applications"""
        df = pd.read_excel(self.file_path, engine='openpyxl')
        return df.to_dict('records')

    def increment_retry_count(self, application_id: str):
        """Increment retry count for an application"""
        df = pd.read_excel(self.file_path, engine='openpyxl')
        mask = df["application_id"] == application_id
        if mask.any():
            df.loc[mask, "retry_count"] = df.loc[mask, "retry_count"].fillna(0).astype(int) + 1
            df.loc[mask, "last_updated"] = datetime.now().isoformat()
            df.to_excel(self.file_path, index=False, engine='openpyxl')


class GoogleSheetsStorage:
    """Google Sheets-based storage for applications"""
    
    def __init__(self, sheets_id: str, credentials_path: str = None):
        try:
            import gspread
            from google.oauth2.service_account import Credentials
            
            self.sheets_id = sheets_id
            
            # Setup credentials
            scopes = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]
            
            if credentials_path:
                creds = Credentials.from_service_account_file(credentials_path, scopes=scopes)
            else:
                # Use default credentials
                creds = Credentials.from_service_account_file(
                    'credentials.json', scopes=scopes
                )
            
            self.client = gspread.authorize(creds)
            self.sheet = self.client.open_by_key(sheets_id).sheet1
            self._initialize_sheet()
            
        except ImportError:
            raise ImportError("gspread and google-auth required for Google Sheets storage")
        except Exception as e:
            logger.error(f"Google Sheets initialization error: {e}")
            raise
    
    def _initialize_sheet(self):
        """Initialize sheet with headers if empty"""
        try:
            headers = self.sheet.row_values(1)
            if not headers:
                self.sheet.append_row([
                    "application_id", "timestamp", "user_email", "user_name",
                    "job_title", "company", "location", "salary", "job_url",
                    "status", "reference_number", "skills_matched",
                    "retry_count", "last_updated"
                ])
        except Exception as e:
            logger.error(f"Sheet initialization error: {e}")
    
    def save(self, application: Dict) -> str:
        """Save application and return application ID"""
        row = [
            application.get("application_id", ""),
            application.get("timestamp", ""),
            application.get("user_email", ""),
            application.get("user_name", ""),
            application.get("job_title", ""),
            application.get("company", ""),
            application.get("location", ""),
            application.get("salary", ""),
            application.get("job_url", ""),
            application.get("status", ""),
            application.get("reference_number", ""),
            application.get("skills_matched", ""),
            application.get("retry_count", 0),
            application.get("last_updated", "")
        ]
        
        self.sheet.append_row(row)
        return application["application_id"]
    
    def get_by_email(self, email: str) -> List[Dict]:
        """Get all applications for a user"""
        all_records = self.sheet.get_all_records()
        return [r for r in all_records if r.get("user_email") == email]
    
    def update_status(self, application_id: str, status: str):
        """Update application status"""
        cell = self.sheet.find(application_id)
        if cell:
            row = cell.row
            # Update status column (column 10)
            self.sheet.update_cell(row, 10, status)
            # Update last_updated column (column 14)
            self.sheet.update_cell(row, 14, datetime.now().isoformat())
    
    def get_all(self) -> List[Dict]:
        """Get all applications"""
        return self.sheet.get_all_records()

    def increment_retry_count(self, application_id: str):
        """Increment retry count for an application"""
        cell = self.sheet.find(application_id)
        if cell:
            row = cell.row
            # retry_count is column 13
            current = self.sheet.cell(row, 13).value
            new_count = (int(current) if current else 0) + 1
            self.sheet.update_cell(row, 13, new_count)
            self.sheet.update_cell(row, 14, datetime.now().isoformat())


class SQLiteStorage:
    """SQLite-based storage for applications"""

    def __init__(self, db_path: str = "./data/jobbot.db"):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._initialize_db()

    def _initialize_db(self):
        """Create applications table if it doesn't exist"""
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS applications (
                    application_id TEXT PRIMARY KEY,
                    timestamp TEXT,
                    user_email TEXT,
                    user_name TEXT,
                    job_title TEXT,
                    company TEXT,
                    location TEXT,
                    salary TEXT,
                    job_url TEXT,
                    status TEXT,
                    reference_number TEXT,
                    skills_matched TEXT,
                    retry_count INTEGER DEFAULT 0,
                    last_updated TEXT
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_applications_email
                ON applications(user_email)
            """)
            conn.commit()
        finally:
            conn.close()

    def save(self, application: Dict) -> str:
        """Save application and return application ID"""
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute(
                """INSERT INTO applications
                   (application_id, timestamp, user_email, user_name, job_title,
                    company, location, salary, job_url, status,
                    reference_number, skills_matched, retry_count, last_updated)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    application.get("application_id", ""),
                    application.get("timestamp", ""),
                    application.get("user_email", ""),
                    application.get("user_name", ""),
                    application.get("job_title", ""),
                    application.get("company", ""),
                    application.get("location", ""),
                    application.get("salary", ""),
                    application.get("job_url", ""),
                    application.get("status", ""),
                    application.get("reference_number", ""),
                    application.get("skills_matched", ""),
                    application.get("retry_count", 0),
                    application.get("last_updated", ""),
                ),
            )
            conn.commit()
        finally:
            conn.close()
        return application["application_id"]

    def get_by_email(self, email: str) -> List[Dict]:
        """Get all applications for a user"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            rows = conn.execute(
                "SELECT * FROM applications WHERE user_email = ?", (email,)
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def update_status(self, application_id: str, status: str):
        """Update application status"""
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute(
                """UPDATE applications SET status = ?, last_updated = ?
                   WHERE application_id = ?""",
                (status, datetime.now().isoformat(), application_id),
            )
            conn.commit()
        finally:
            conn.close()

    def get_all(self) -> List[Dict]:
        """Get all applications"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            rows = conn.execute("SELECT * FROM applications").fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def increment_retry_count(self, application_id: str):
        """Increment retry count for an application"""
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute(
                """UPDATE applications
                   SET retry_count = COALESCE(retry_count, 0) + 1,
                       last_updated = ?
                   WHERE application_id = ?""",
                (datetime.now().isoformat(), application_id),
            )
            conn.commit()
        finally:
            conn.close()


class ApplicationTracker:
    """Main application tracker with storage abstraction"""

    def __init__(self, storage_type: str = "excel", config: Dict = None):
        config = config or {}

        if storage_type == "excel":
            self.storage = ExcelStorage(config.get("excel_path", "./data/applications.xlsx"))
        elif storage_type == "google_sheets":
            self.storage = GoogleSheetsStorage(
                config.get("sheets_id"),
                config.get("credentials_path")
            )
        elif storage_type == "sqlite":
            self.storage = SQLiteStorage(config.get("sqlite_path", "./data/jobbot.db"))
        else:
            raise ValueError(f"Unknown storage type: {storage_type}")
    
    def save_application(self, application: Dict) -> str:
        """
        Save application and return application ID
        
        Args:
            application: Application dictionary with job and user info
            
        Returns:
            Application ID
        """
        # Generate application ID if not provided
        if "application_id" not in application:
            application["application_id"] = str(uuid.uuid4())
        
        # Add timestamp if not provided
        if "timestamp" not in application:
            application["timestamp"] = datetime.now().isoformat()
        
        # Set default status
        if "status" not in application:
            application["status"] = "pending"
        
        # Set retry count
        if "retry_count" not in application:
            application["retry_count"] = 0
        
        # Set last updated
        application["last_updated"] = datetime.now().isoformat()
        
        # Convert skills list to string
        if isinstance(application.get("skills_matched"), list):
            application["skills_matched"] = ", ".join(application["skills_matched"])
        
        return self.storage.save(application)
    
    def get_user_applications(self, email: str) -> List[Dict]:
        """
        Retrieve all applications for a user
        
        Args:
            email: User's email address
            
        Returns:
            List of application dictionaries
        """
        return self.storage.get_by_email(email)
    
    def update_status(self, application_id: str, status: str):
        """
        Update application status
        
        Args:
            application_id: Application ID
            status: New status (pending, submitted, failed)
        """
        self.storage.update_status(application_id, status)
    
    def get_statistics(self, email: str) -> Dict:
        """
        Calculate application statistics for a user
        
        Args:
            email: User's email address
            
        Returns:
            Statistics dictionary
        """
        applications = self.get_user_applications(email)
        
        total = len(applications)
        pending = sum(1 for app in applications if app.get("status") == "pending")
        submitted = sum(1 for app in applications if app.get("status") == "submitted")
        failed = sum(1 for app in applications if app.get("status") == "failed")
        
        return {
            "total": total,
            "pending": pending,
            "submitted": submitted,
            "failed": failed,
            "success_rate": (submitted / total * 100) if total > 0 else 0
        }
    
    def increment_retry_count(self, application_id: str):
        """Increment retry count for an application"""
        self.storage.increment_retry_count(application_id)
