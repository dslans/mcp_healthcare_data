#!/usr/bin/env python3
"""
Test script for Healthcare Analytics MCP Server

This script validates that all tools are working correctly with the Tuva Health data.
Run this after setting up your environment to ensure everything is configured properly.
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_bigquery_connection():
    """Test basic BigQuery connectivity."""
    print("🔍 Testing BigQuery connection...")
    try:
        from google.cloud import bigquery
        from google.oauth2 import service_account
        
        project_id = os.getenv('GCP_PROJECT_ID')
        credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        
        if credentials_path and os.path.exists(credentials_path):
            # Use service account JSON file
            credentials = service_account.Credentials.from_service_account_file(credentials_path)
            client = bigquery.Client(project=project_id, credentials=credentials)
            print(f"  Using service account: {credentials_path}")
        else:
            # Use Application Default Credentials (ADC)
            client = bigquery.Client(project=project_id)
            print("  Using Application Default Credentials (ADC)")
        
        # Simple query to test connection
        query = "SELECT 1 as test_value"
        job = client.query(query)
        result = job.result()
        
        for row in result:
            if row.test_value == 1:
                print("✅ BigQuery connection successful!")
                return True
                
    except Exception as e:
        print(f"❌ BigQuery connection failed: {e}")
        return False

def test_tuva_data_access():
    """Test access to Tuva Health datasets."""
    print("\n🏥 Testing Tuva Health data access...")
    try:
        from google.cloud import bigquery
        client = bigquery.Client(project=os.getenv('GCP_PROJECT_ID'))
        
        dataset_prefix = os.getenv('BIGQUERY_DATASET_PREFIX', '')
        
        # Test core patient data
        query = f"""
        SELECT COUNT(*) as patient_count
        FROM `{dataset_prefix}core.patient`
        LIMIT 1
        """
        
        job = client.query(query)
        result = job.result()
        
        for row in result:
            patient_count = row.patient_count
            print(f"✅ Found {patient_count:,} patients in core.patient table")
            return True
            
    except Exception as e:
        print(f"❌ Tuva data access failed: {e}")
        return False

def test_mcp_tools():
    """Test MCP server tools."""
    print("\n🔧 Testing MCP server tools...")
    
    try:
        # Import our healthcare server module
        import healthcare_mcp_server as hms
        
        # Test 1: Patient Demographics
        print("  Testing get_patient_demographics...")
        demographics = hms.get_patient_demographics(
            start_date="2018-01-01",
            end_date="2018-12-31"
        )
        print(f"    ✅ Found {demographics.get('total_patients', 0):,} patients")
        
        # Test 2: Utilization Summary
        print("  Testing get_utilization_summary...")
        utilization = hms.get_utilization_summary(
            start_date="2018-01-01",
            end_date="2018-12-31"
        )
        print(f"    ✅ Found {utilization.get('total_claims', 0):,} claims")
        
        # Test 3: PMPM Analysis
        print("  Testing get_pmpm_analysis...")
        pmpm = hms.get_pmpm_analysis(
            start_date="2018-01-01",
            end_date="2018-12-31"
        )
        print(f"    ✅ Analyzed {pmpm.get('months_analyzed', 0)} months of data")
        
        # Test 4: Quality Measures
        print("  Testing get_quality_measures_summary...")
        quality = hms.get_quality_measures_summary(year="2022")
        print(f"    ✅ Found {quality.get('measures_count', 0)} quality measures")
        
        print("\n🎉 All MCP tools tested successfully!")
        return True
        
    except Exception as e:
        print(f"❌ MCP tools test failed: {e}")
        return False

def test_server_startup():
    """Test that the MCP server can start up properly."""
    print("\n🚀 Testing MCP server startup...")
    
    try:
        # Import the server module to check for import errors
        import healthcare_mcp_server
        print("✅ Server module imported successfully")
        
        # Check that the FastMCP instance is properly configured
        mcp_instance = healthcare_mcp_server.mcp
        print(f"✅ FastMCP server configured: {mcp_instance.name}")
        
        return True
        
    except Exception as e:
        print(f"❌ Server startup test failed: {e}")
        return False

def print_environment_info():
    """Print current environment configuration."""
    print("\n📋 Environment Configuration:")
    print(f"  Python version: {sys.version.split()[0]}")
    print(f"  GCP Project ID: {os.getenv('GCP_PROJECT_ID', 'Not set')}")
    print(f"  Dataset Prefix: {os.getenv('BIGQUERY_DATASET_PREFIX', 'Not set')}")
    print(f"  Credentials Path: {os.getenv('GOOGLE_APPLICATION_CREDENTIALS', 'Not set')}")

def main():
    """Run all tests."""
    print("Healthcare Analytics MCP Server - Test Suite")
    print("=" * 50)
    
    print_environment_info()
    
    # Run tests in order
    tests = [
        test_bigquery_connection,
        test_tuva_data_access, 
        test_server_startup,
        test_mcp_tools
    ]
    
    passed_tests = 0
    total_tests = len(tests)
    
    for test in tests:
        if test():
            passed_tests += 1
        print()  # Add spacing between tests
    
    # Print summary
    print("=" * 50)
    print(f"Test Summary: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All tests passed! Your healthcare MCP server is ready to use.")
        print("\nTo start the server, run:")
        print("  fastmcp run healthcare_mcp_server.py")
    else:
        print("❌ Some tests failed. Please check your configuration.")
        print("\nCommon issues:")
        print("  1. Verify your .env file is configured correctly")
        print("  2. Ensure your Google Cloud credentials are valid")
        print("  3. Check that Tuva Health data is loaded in BigQuery")

if __name__ == "__main__":
    main()
