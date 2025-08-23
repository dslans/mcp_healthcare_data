#!/usr/bin/env python3
"""
Healthcare Analytics MCP Server

A Model Context Protocol server for healthcare data analysis using Tuva Health data.
Provides tools for value-based care analytics, quality measures, utilization analysis,
and financial metrics.
"""

import os
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, date
import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account
from dotenv import load_dotenv

from fastmcp import FastMCP

# Load environment variables
load_dotenv()

def create_bigquery_client():
    """Create BigQuery client with flexible authentication."""
    project_id = os.getenv('GCP_PROJECT_ID')
    credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    
    if credentials_path and os.path.exists(credentials_path):
        # Use service account JSON file
        credentials = service_account.Credentials.from_service_account_file(credentials_path)
        client = bigquery.Client(project=project_id, credentials=credentials)
        print(f"Using service account credentials from: {credentials_path}")
    else:
        # Use Application Default Credentials (ADC)
        client = bigquery.Client(project=project_id)
        print("Using Application Default Credentials (ADC)")
    
    return client

# Initialize BigQuery client
client = create_bigquery_client()

# Initialize FastMCP server
mcp = FastMCP("Healthcare Analytics Server")

# Configuration
DATASET_PREFIX = os.getenv('BIGQUERY_DATASET_PREFIX', '')

def execute_query(query: str) -> pd.DataFrame:
    """Execute a BigQuery query and return results as a DataFrame."""
    try:
        job = client.query(query)
        return job.to_dataframe()
    except Exception as e:
        raise Exception(f"Query execution failed: {str(e)}")

def format_currency(amount: float) -> str:
    """Format amount as currency."""
    return f"${amount:,.2f}"

def format_percentage(value: float) -> str:
    """Format value as percentage."""
    return f"{value:.1f}%"

@mcp.tool()
def get_patient_demographics(
    start_date: str = "2022-01-01",
    end_date: str = "2022-12-31",
    age_groups: bool = True
) -> Dict[str, Any]:
    """
    Get patient demographic summary for the specified period.
    
    Args:
        start_date: Start date for analysis (YYYY-MM-DD format)
        end_date: End date for analysis (YYYY-MM-DD format) 
        age_groups: Whether to include age group breakdown
        
    Returns:
        Dictionary containing demographic statistics
    """
    base_query = f"""
    SELECT 
        COUNT(DISTINCT patient_id) as total_patients,
        AVG(EXTRACT(YEAR FROM CURRENT_DATE()) - birth_year) as avg_age,
        COUNTIF(gender = 'female') / COUNT(*) * 100 as female_pct,
        COUNTIF(gender = 'male') / COUNT(*) * 100 as male_pct
    FROM `{DATASET_PREFIX}core.patient` p
    INNER JOIN `{DATASET_PREFIX}core.eligibility` e ON p.patient_id = e.patient_id
    WHERE e.enrollment_start_date <= '{end_date}'
      AND e.enrollment_end_date >= '{start_date}'
    """
    
    df = execute_query(base_query)
    result = df.iloc[0].to_dict()
    
    if age_groups:
        age_group_query = f"""
        SELECT 
            CASE 
                WHEN age < 18 THEN '0-17'
                WHEN age BETWEEN 18 AND 34 THEN '18-34'
                WHEN age BETWEEN 35 AND 54 THEN '35-54'
                WHEN age BETWEEN 55 AND 64 THEN '55-64'
                WHEN age >= 65 THEN '65+'
            END as age_group,
            COUNT(*) as count,
            COUNT(*) / SUM(COUNT(*)) OVER() * 100 as percentage
        FROM (
            SELECT 
                patient_id,
                EXTRACT(YEAR FROM CURRENT_DATE()) - birth_year as age
            FROM `{DATASET_PREFIX}core.patient` p
            INNER JOIN `{DATASET_PREFIX}core.eligibility` e ON p.patient_id = e.patient_id
            WHERE e.enrollment_start_date <= '{end_date}'
              AND e.enrollment_end_date >= '{start_date}'
        )
        GROUP BY age_group
        ORDER BY age_group
        """
        
        age_df = execute_query(age_group_query)
        result['age_groups'] = age_df.to_dict('records')
    
    return result

@mcp.tool()
def get_utilization_summary(
    start_date: str = "2022-01-01",
    end_date: str = "2022-12-31",
    service_category: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get healthcare utilization summary for the specified period.
    
    Args:
        start_date: Start date for analysis (YYYY-MM-DD format)
        end_date: End date for analysis (YYYY-MM-DD format)
        service_category: Optional filter for specific service category
        
    Returns:
        Dictionary containing utilization metrics
    """
    where_clause = f"WHERE claim_start_date BETWEEN '{start_date}' AND '{end_date}'"
    if service_category:
        where_clause += f" AND service_category_1 = '{service_category}'"
    
    query = f"""
    WITH utilization_stats AS (
        SELECT 
            COUNT(DISTINCT claim_id) as total_claims,
            COUNT(DISTINCT patient_id) as unique_patients,
            SUM(paid_amount) as total_paid,
            SUM(allowed_amount) as total_allowed,
            AVG(paid_amount) as avg_paid_per_claim,
            AVG(allowed_amount) as avg_allowed_per_claim
        FROM `{DATASET_PREFIX}core.medical_claim`
        {where_clause}
    ),
    service_breakdown AS (
        SELECT 
            service_category_1,
            COUNT(*) as claim_count,
            SUM(paid_amount) as total_paid,
            COUNT(*) / SUM(COUNT(*)) OVER() * 100 as percentage_of_claims
        FROM `{DATASET_PREFIX}core.medical_claim`
        {where_clause}
        GROUP BY service_category_1
        ORDER BY claim_count DESC
        LIMIT 10
    )
    SELECT * FROM utilization_stats
    """
    
    df = execute_query(query)
    result = df.iloc[0].to_dict()
    
    # Get service category breakdown
    service_query = f"""
    SELECT 
        service_category_1,
        COUNT(*) as claim_count,
        SUM(paid_amount) as total_paid,
        COUNT(*) / SUM(COUNT(*)) OVER() * 100 as percentage_of_claims
    FROM `{DATASET_PREFIX}core.medical_claim`
    {where_clause}
    GROUP BY service_category_1
    ORDER BY claim_count DESC
    LIMIT 10
    """
    
    service_df = execute_query(service_query)
    result['top_service_categories'] = service_df.to_dict('records')
    
    return result

@mcp.tool() 
def get_pmpm_analysis(
    start_date: str = "2022-01-01",
    end_date: str = "2022-12-31",
    payer: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get Per Member Per Month (PMPM) financial analysis.
    
    Args:
        start_date: Start date for analysis (YYYY-MM-DD format)
        end_date: End date for analysis (YYYY-MM-DD format)
        payer: Optional filter for specific payer
        
    Returns:
        Dictionary containing PMPM metrics
    """
    where_clause = f"WHERE year_month BETWEEN '{start_date[:7]}' AND '{end_date[:7]}'"
    if payer:
        where_clause += f" AND payer = '{payer}'"
    
    query = f"""
    SELECT 
        AVG(total_allowed_pmpm) as avg_total_allowed_pmpm,
        AVG(total_paid_pmpm) as avg_total_paid_pmpm,
        AVG(inpatient_allowed_pmpm) as avg_inpatient_allowed_pmpm,
        AVG(outpatient_allowed_pmpm) as avg_outpatient_allowed_pmpm,
        AVG(office_visit_allowed_pmpm) as avg_office_visit_allowed_pmpm,
        AVG(ancillary_allowed_pmpm) as avg_ancillary_allowed_pmpm,
        COUNT(DISTINCT year_month) as months_analyzed,
        SUM(member_months) as total_member_months
    FROM `{DATASET_PREFIX}financial_pmpm.pmpm_payer`
    {where_clause}
    """
    
    df = execute_query(query)
    result = df.iloc[0].to_dict()
    
    # Get trend analysis
    trend_query = f"""
    SELECT 
        year_month,
        AVG(total_allowed_pmpm) as monthly_allowed_pmpm,
        AVG(total_paid_pmpm) as monthly_paid_pmpm,
        SUM(member_months) as member_months
    FROM `{DATASET_PREFIX}financial_pmpm.pmpm_payer`
    {where_clause}
    GROUP BY year_month
    ORDER BY year_month
    """
    
    trend_df = execute_query(trend_query)
    result['monthly_trends'] = trend_df.to_dict('records')
    
    return result

@mcp.tool()
def get_quality_measures_summary(
    measure_name: Optional[str] = None,
    year: str = "2022"
) -> Dict[str, Any]:
    """
    Get quality measures summary for the specified year.
    
    Args:
        measure_name: Optional filter for specific measure
        year: Year for analysis (YYYY format)
        
    Returns:
        Dictionary containing quality measure results
    """
    where_clause = f"WHERE performance_period_end LIKE '{year}%'"
    if measure_name:
        where_clause += f" AND measure_name = '{measure_name}'"
    
    query = f"""
    SELECT 
        measure_name,
        measure_version,
        numerator,
        denominator,
        ROUND(performance_rate * 100, 2) as performance_rate_pct,
        performance_flag
    FROM `{DATASET_PREFIX}quality_measures.summary_wide`
    {where_clause}
    ORDER BY measure_name
    """
    
    df = execute_query(query)
    result = {
        'measures_count': len(df),
        'measures': df.to_dict('records')
    }
    
    if len(df) > 0:
        result['avg_performance_rate'] = df['performance_rate_pct'].mean()
        result['measures_meeting_target'] = (df['performance_flag'] == 'Pass').sum()
    
    return result

@mcp.tool()
def get_chronic_conditions_prevalence(
    condition_category: Optional[str] = None,
    year: str = "2022"
) -> Dict[str, Any]:
    """
    Get chronic conditions prevalence analysis.
    
    Args:
        condition_category: Optional filter for specific condition category
        year: Year for analysis (YYYY format)
        
    Returns:
        Dictionary containing chronic condition prevalence
    """
    where_clause = f"WHERE condition_date LIKE '{year}%'"
    if condition_category:
        where_clause += f" AND condition_family = '{condition_category}'"
    
    query = f"""
    SELECT 
        condition_family,
        COUNT(DISTINCT patient_id) as patient_count,
        COUNT(DISTINCT patient_id) / (
            SELECT COUNT(DISTINCT patient_id) 
            FROM `{DATASET_PREFIX}core.condition` 
            WHERE condition_date LIKE '{year}%'
        ) * 100 as prevalence_rate
    FROM `{DATASET_PREFIX}chronic_conditions.tuva_chronic_conditions_long`
    {where_clause}
    GROUP BY condition_family
    ORDER BY patient_count DESC
    LIMIT 20
    """
    
    df = execute_query(query)
    result = {
        'conditions_analyzed': len(df),
        'conditions': df.to_dict('records')
    }
    
    return result

@mcp.tool()
def get_high_cost_patients(
    cost_threshold: float = 10000.0,
    year: str = "2022",
    limit: int = 100
) -> Dict[str, Any]:
    """
    Identify high-cost patients for case management.
    
    Args:
        cost_threshold: Minimum cost threshold to be considered high-cost
        year: Year for analysis (YYYY format)  
        limit: Maximum number of patients to return
        
    Returns:
        Dictionary containing high-cost patient information
    """
    query = f"""
    WITH patient_costs AS (
        SELECT 
            patient_id,
            SUM(paid_amount) as total_paid,
            SUM(allowed_amount) as total_allowed,
            COUNT(DISTINCT claim_id) as total_claims,
            COUNT(DISTINCT CASE WHEN claim_type = 'institutional' THEN claim_id END) as inpatient_claims,
            COUNT(DISTINCT CASE WHEN claim_type = 'professional' THEN claim_id END) as outpatient_claims
        FROM `{DATASET_PREFIX}core.medical_claim`
        WHERE EXTRACT(YEAR FROM claim_start_date) = {year}
        GROUP BY patient_id
        HAVING total_paid >= {cost_threshold}
        ORDER BY total_paid DESC
        LIMIT {limit}
    )
    SELECT 
        pc.*,
        p.birth_year,
        p.gender,
        EXTRACT(YEAR FROM CURRENT_DATE()) - p.birth_year as age
    FROM patient_costs pc
    JOIN `{DATASET_PREFIX}core.patient` p ON pc.patient_id = p.patient_id
    ORDER BY pc.total_paid DESC
    """
    
    df = execute_query(query)
    
    result = {
        'high_cost_patient_count': len(df),
        'total_cost_all_patients': df['total_paid'].sum() if len(df) > 0 else 0,
        'avg_cost_per_patient': df['total_paid'].mean() if len(df) > 0 else 0,
        'patients': df.to_dict('records')
    }
    
    return result

@mcp.tool()
def get_readmissions_analysis(
    year: str = "2022",
    condition_category: Optional[str] = None
) -> Dict[str, Any]:
    """
    Analyze 30-day readmission rates and patterns.
    
    Args:
        year: Year for analysis (YYYY format)
        condition_category: Optional filter for specific condition category
        
    Returns:
        Dictionary containing readmission analysis
    """
    where_clause = f"WHERE encounter_start_date LIKE '{year}%'"
    if condition_category:
        where_clause += f" AND primary_diagnosis_description LIKE '%{condition_category}%'"
    
    query = f"""
    SELECT 
        COUNT(DISTINCT encounter_id) as total_encounters,
        COUNT(DISTINCT CASE WHEN readmission_flag = 1 THEN encounter_id END) as readmissions,
        COUNT(DISTINCT CASE WHEN readmission_flag = 1 THEN encounter_id END) / COUNT(DISTINCT encounter_id) * 100 as readmission_rate,
        AVG(length_of_stay) as avg_los,
        SUM(total_paid) as total_cost
    FROM `{DATASET_PREFIX}readmissions.encounter_augmented`
    {where_clause}
    """
    
    df = execute_query(query)
    result = df.iloc[0].to_dict()
    
    return result

@mcp.tool()
def get_hcc_risk_scores(
    year: str = "2022",
    limit: int = 1000
) -> Dict[str, Any]:
    """
    Get HCC risk score analysis for patient population.
    
    Args:
        year: Year for analysis (YYYY format)
        limit: Maximum number of patients to analyze
        
    Returns:
        Dictionary containing HCC risk score statistics
    """
    query = f"""
    SELECT 
        patient_id,
        hcc_risk_score,
        COUNT(DISTINCT hcc_code) as hcc_condition_count
    FROM `{DATASET_PREFIX}cms_hcc.patient_risk_scores`
    WHERE payment_year = {year}
    ORDER BY hcc_risk_score DESC
    LIMIT {limit}
    """
    
    df = execute_query(query)
    
    result = {
        'patients_analyzed': len(df),
        'avg_risk_score': df['hcc_risk_score'].mean() if len(df) > 0 else 0,
        'median_risk_score': df['hcc_risk_score'].median() if len(df) > 0 else 0,
        'high_risk_patients': (df['hcc_risk_score'] > 2.0).sum() if len(df) > 0 else 0,
        'low_risk_patients': (df['hcc_risk_score'] < 1.0).sum() if len(df) > 0 else 0,
        'risk_score_distribution': df['hcc_risk_score'].describe().to_dict() if len(df) > 0 else {}
    }
    
    return result

if __name__ == "__main__":
    mcp.run()
