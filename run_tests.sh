#!/bin/bash

# Test Runner Script for AI Job Recommendation Bot

echo "🧪 Running Tests for AI Job Recommendation Bot"
echo "=============================================="
echo ""

# Activate conda environment
eval "$(conda shell.bash hook)"
conda activate jobbot

# Run unit tests
echo "📝 Running Unit Tests..."
echo "------------------------"
pytest tests/unit/ -v --tb=short

UNIT_EXIT=$?

echo ""
echo "------------------------"
echo ""

# Run integration tests
echo "🔗 Running Integration Tests..."
echo "------------------------"
pytest tests/integration/ -v --tb=short

INTEGRATION_EXIT=$?

echo ""
echo "=============================================="
echo "📊 Test Summary"
echo "=============================================="

if [ $UNIT_EXIT -eq 0 ]; then
    echo "✅ Unit Tests: PASSED"
else
    echo "❌ Unit Tests: FAILED"
fi

if [ $INTEGRATION_EXIT -eq 0 ]; then
    echo "✅ Integration Tests: PASSED"
else
    echo "❌ Integration Tests: FAILED"
fi

echo ""

# Overall result
if [ $UNIT_EXIT -eq 0 ] && [ $INTEGRATION_EXIT -eq 0 ]; then
    echo "🎉 All tests passed!"
    exit 0
else
    echo "⚠️  Some tests failed. Check output above."
    exit 1
fi
