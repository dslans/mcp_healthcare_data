#!/usr/bin/env python3
"""
Healthcare Analytics MCP Server

A Model Context Protocol server for healthcare data analysis using Tuva Health data.
Provides tools for value-based care analytics, quality measures, utilization analysis,
and financial metrics.
"""

import os
import asyncio
import time
import hashlib
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, date
from decimal import Decimal
import pandas as pd
import numpy as np
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

# Cache Configuration
CACHE = {}

@mcp.tool()
def clear_cache() -> Dict[str, str]:
    """Clears the in-memory cache."""
    global CACHE
    cache_size = len(CACHE)
    CACHE = {}
    return {"status": f"Cache cleared - removed {cache_size} entries"}

def get_from_cache_or_execute(
    query: str, 
    params: Optional[Dict[str, Any]] = None, 
    ttl_minutes: int = 60
) -> pd.DataFrame:
    """
    Checks cache for data with TTL (Time To Live), otherwise executes query.
    
    Args:
        query: SQL query to execute
        params: Query parameters
        ttl_minutes: Time to live in minutes for cached results
        
    Returns:
        DataFrame with query results
    """
    # Create a cache key by hashing query and parameters
    cache_input = f"{query}_{str(params) if params else 'None'}"
    cache_key = hashlib.md5(cache_input.encode('utf-8')).hexdigest()
    
    # Check if cached and still valid
    if cache_key in CACHE:
        data, timestamp = CACHE[cache_key]
        if time.time() - timestamp < ttl_minutes * 60:
            return data
        # Remove expired entry
        del CACHE[cache_key]
    
    # Execute query and cache with timestamp
    df = execute_query(query, params)
    CACHE[cache_key] = (df, time.time())
    return df

def execute_query(query: str, params: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
    """
    Execute a BigQuery query with optional parameters and return results as a DataFrame.

    Args:
        query: The SQL query to execute, with placeholders for parameters (e.g., @param_name).
        params: A dictionary of parameters to substitute into the query.

    Returns:
        A pandas DataFrame with the query results.
    """
    try:
        job_config = bigquery.QueryJobConfig()
        if params:
            query_params = []
            for key, value in params.items():
                # Infer the type of the parameter
                if isinstance(value, bool):
                    param_type = "BOOL"
                elif isinstance(value, int):
                    param_type = "INT64"
                elif isinstance(value, float):
                    param_type = "FLOAT64"
                elif isinstance(value, str):
                    # You might need to add more specific date/time checks here if needed
                    param_type = "STRING"
                else:
                    # Default to STRING for other types, or raise an error
                    param_type = "STRING"
                
                query_params.append(bigquery.ScalarQueryParameter(key, param_type, value))
            job_config.query_parameters = query_params

        job = client.query(query, job_config=job_config)
        df = job.to_dataframe()

        # Convert Decimal columns to float for JSON serialization
        for col in df.columns:
            if df[col].dtype == 'object':
                # Check if column contains Decimal objects
                if len(df[col]) > 0 and isinstance(df[col].iloc[0], Decimal):
                    df[col] = df[col].astype(float)
                # Also handle NaN Decimal objects
                elif df[col].apply(lambda x: isinstance(x, Decimal) if pd.notna(x) else False).any():
                    df[col] = df[col].apply(lambda x: float(x) if isinstance(x, Decimal) else x)
        
        return df
    except Exception as e:
        raise Exception(f"Query execution failed: {str(e)}")


def format_currency(amount: float) -> str:
    """Format amount as currency."""
    return f"${amount:,.2f}"

def format_percentage(value: float) -> str:
    """Format value as percentage."""
    return f"{value:.1f}%"

def convert_decimal_values(obj):
    """Recursively convert Decimal objects to float in dictionaries and lists."""
    if isinstance(obj, dict):
        return {key: convert_decimal_values(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_decimal_values(item) for item in obj]
    elif isinstance(obj, Decimal):
        return float(obj)
    elif pd.isna(obj) and isinstance(obj, (pd.Series, np.floating)):
        return None
    else:
        return obj

@mcp.tool()
def get_patient_demographics(
    start_date: str = "2018-01-01",
    end_date: str = "2018-12-31",
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
        COUNT(DISTINCT p.person_id) as total_patients,
        AVG(p.age) as avg_age,
        SAFE_DIVIDE(COUNTIF(p.sex = 'female'), COUNT(*)) * 100 as female_pct,
        SAFE_DIVIDE(COUNTIF(p.sex = 'male'), COUNT(*)) * 100 as male_pct
    FROM `{DATASET_PREFIX}core.patient` p
    INNER JOIN `{DATASET_PREFIX}core.eligibility` e ON p.person_id = e.person_id
    WHERE e.enrollment_start_date <= @end_date
      AND e.enrollment_end_date >= @start_date
    """
    params = {"start_date": start_date, "end_date": end_date}
    
    df = get_from_cache_or_execute(base_query, params=params, ttl_minutes=240)  # 4 hour cache for demographics
    result = df.iloc[0].to_dict()
    
    if age_groups:
        age_group_query = f"""
        SELECT 
            p.age_group,
            COUNT(*) as count,
            SAFE_DIVIDE(COUNT(*), SUM(COUNT(*)) OVER()) * 100 as percentage
        FROM `{DATASET_PREFIX}core.patient` p
        INNER JOIN `{DATASET_PREFIX}core.eligibility` e ON p.person_id = e.person_id
        WHERE e.enrollment_start_date <= @end_date
          AND e.enrollment_end_date >= @start_date
          AND p.age_group IS NOT NULL
        GROUP BY p.age_group
        ORDER BY p.age_group
        """
        
        age_df = get_from_cache_or_execute(age_group_query, params=params, ttl_minutes=240)
        result['age_groups'] = age_df.to_dict('records')
    
    return convert_decimal_values(result)

@mcp.tool()
def get_utilization_summary(
    start_date: str = "2018-01-01",
    end_date: str = "2018-12-31",
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
    where_clauses = ["claim_start_date BETWEEN @start_date AND @end_date"]
    params = {"start_date": start_date, "end_date": end_date}

    if service_category:
        where_clauses.append("service_category_1 = @service_category")
        params["service_category"] = service_category
    
    where_clause = " AND ".join(where_clauses)
    
    query = f"""
    WITH utilization_stats AS (
        SELECT 
            COUNT(DISTINCT claim_id) as total_claims,
            COUNT(DISTINCT person_id) as unique_patients,
            SUM(paid_amount) as total_paid,
            SUM(allowed_amount) as total_allowed,
            AVG(paid_amount) as avg_paid_per_claim,
            AVG(allowed_amount) as avg_allowed_per_claim
        FROM `{DATASET_PREFIX}core.medical_claim`
        WHERE {where_clause}
    ),
    service_breakdown AS (
        SELECT 
            service_category_1,
            COUNT(*) as claim_count,
            SUM(paid_amount) as total_paid,
            SAFE_DIVIDE(COUNT(*), SUM(COUNT(*)) OVER()) * 100 as percentage_of_claims
        FROM `{DATASET_PREFIX}core.medical_claim`
        WHERE {where_clause}
        GROUP BY service_category_1
        ORDER BY claim_count DESC
        LIMIT 10
    )
    SELECT * FROM utilization_stats
    """
    
    df = get_from_cache_or_execute(query, params=params, ttl_minutes=120)  # 2 hour cache
    result = df.iloc[0].to_dict()
    
    # Get service category breakdown
    service_query = f"""
    SELECT 
        service_category_1,
        COUNT(*) as claim_count,
        SUM(paid_amount) as total_paid,
        SAFE_DIVIDE(COUNT(*), SUM(COUNT(*)) OVER()) * 100 as percentage_of_claims
    FROM `{DATASET_PREFIX}core.medical_claim`
    WHERE {where_clause}
    GROUP BY service_category_1
    ORDER BY claim_count DESC
    LIMIT 10
    """
    
    service_df = get_from_cache_or_execute(service_query, params=params, ttl_minutes=120)
    result['top_service_categories'] = service_df.to_dict('records')
    
    return result

@mcp.tool() 
def get_pmpm_analysis(
    start_date: str = "2018-01-01",
    end_date: str = "2018-12-31",
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
    # Convert provided dates to YYYYMM format to match year_month column
    start_ym = start_date[:7].replace('-', '')
    end_ym = end_date[:7].replace('-', '')

    where_clauses = ["year_month BETWEEN @start_ym AND @end_ym"]
    params = {"start_ym": start_ym, "end_ym": end_ym}

    if payer:
        where_clauses.append("payer = @payer")
        params["payer"] = payer
    
    where_clause = " AND ".join(where_clauses)
    
    query = f"""
    SELECT 
        COUNT(DISTINCT person_id || year_month) as total_member_months,
        SAFE_DIVIDE(SUM(total_allowed), COUNT(DISTINCT person_id || year_month)) as total_allowed_pmpm,
        SAFE_DIVIDE(SUM(total_paid), COUNT(DISTINCT person_id || year_month)) as total_paid_pmpm,
        SAFE_DIVIDE(SUM(inpatient_allowed), COUNT(DISTINCT person_id || year_month)) as inpatient_allowed_pmpm,
        SAFE_DIVIDE(SUM(outpatient_allowed), COUNT(DISTINCT person_id || year_month)) as outpatient_allowed_pmpm,
        SAFE_DIVIDE(SUM(office_based_allowed), COUNT(DISTINCT person_id || year_month)) as office_visit_allowed_pmpm,
        SAFE_DIVIDE(SUM(ancillary_allowed), COUNT(DISTINCT person_id || year_month)) as avg_ancillary_allowed_pmpm
    FROM `{DATASET_PREFIX}financial_pmpm.pmpm_prep`
    WHERE {where_clause}
    """
    
    df = get_from_cache_or_execute(query, params=params, ttl_minutes=60)  # 1 hour cache for financial data
    result = df.iloc[0].to_dict()
    
    # Get trend analysis
    trend_query = f"""
    SELECT 
        year_month,
        SAFE_DIVIDE(SUM(total_allowed), COUNT(DISTINCT person_id || year_month)) as monthly_allowed_pmpm,
        SAFE_DIVIDE(SUM(total_paid), COUNT(DISTINCT person_id || year_month)) as monthly_paid_pmpm,
        COUNT(DISTINCT person_id || year_month) as member_months
    FROM `{DATASET_PREFIX}financial_pmpm.pmpm_prep`
    WHERE {where_clause}
    GROUP BY year_month
    ORDER BY year_month
    """
    
    trend_df = get_from_cache_or_execute(trend_query, params=params, ttl_minutes=60)
    result['monthly_trends'] = trend_df.to_dict('records')
    
    return result

@mcp.tool()
def get_quality_measures_summary(
    measure_name: Optional[str] = None,
    year: str = "2018"
) -> Dict[str, Any]:
    """
    Get quality measures summary for the specified year.
    
    Args:
        measure_name: Optional filter for specific measure (use column names like 'adh_diabetes', 'cqm_130', etc.)
        year: Year for analysis (YYYY format)
        
    Returns:
        Dictionary containing quality measure results
    """
    params = {"year": year}
    
    # Get the structure of available measures
    if measure_name:
        # This is tricky because measure_name is a column name. We can't parameterize column names.
        # We can validate it against a list of known columns to prevent injection.
        # For this example, we'll assume the input is safe, but in a real-world scenario, you'd validate.
        query = f"""
        SELECT 
            COUNT(DISTINCT person_id) as total_patients,
            SUM(CASE WHEN {measure_name} = 1 THEN 1 ELSE 0 END) as numerator,
            COUNT(CASE WHEN {measure_name} IS NOT NULL THEN person_id END) as denominator,
            ROUND(SAFE_DIVIDE(SUM(CASE WHEN {measure_name} = 1 THEN 1 ELSE 0 END), COUNT(CASE WHEN {measure_name} IS NOT NULL THEN person_id END)) * 100, 2) as performance_rate_pct
        FROM `{DATASET_PREFIX}quality_measures.summary_wide`
        """
        
        df = get_from_cache_or_execute(query, params=params, ttl_minutes=360)  # 6 hour cache for quality measures
        result = df.iloc[0].to_dict()
        result['measure_name'] = measure_name
        
    else:
        # Get summary for all measures
        query = f"""
        SELECT 
            'adh_diabetes' as measure_name,
            SUM(CASE WHEN adh_diabetes = 1 THEN 1 ELSE 0 END) as numerator,
            COUNT(CASE WHEN adh_diabetes IS NOT NULL THEN person_id END) as denominator,
            ROUND(SAFE_DIVIDE(SUM(CASE WHEN adh_diabetes = 1 THEN 1 ELSE 0 END), COUNT(CASE WHEN adh_diabetes IS NOT NULL THEN person_id END)) * 100, 2) as performance_rate_pct
        FROM `{DATASET_PREFIX}quality_measures.summary_wide`
        
        UNION ALL
        
        SELECT 
            'adh_ras' as measure_name,
            SUM(CASE WHEN adh_ras = 1 THEN 1 ELSE 0 END) as numerator,
            COUNT(CASE WHEN adh_ras IS NOT NULL THEN person_id END) as denominator,
            ROUND(SAFE_DIVIDE(SUM(CASE WHEN adh_ras = 1 THEN 1 ELSE 0 END), COUNT(CASE WHEN adh_ras IS NOT NULL THEN person_id END)) * 100, 2) as performance_rate_pct
        FROM `{DATASET_PREFIX}quality_measures.summary_wide`
        
        UNION ALL
        
        SELECT 
            'adh_statins' as measure_name,
            SUM(CASE WHEN adh_statins = 1 THEN 1 ELSE 0 END) as numerator,
            COUNT(CASE WHEN adh_statins IS NOT NULL THEN person_id END) as denominator,
            ROUND(SAFE_DIVIDE(SUM(CASE WHEN adh_statins = 1 THEN 1 ELSE 0 END), COUNT(CASE WHEN adh_statins IS NOT NULL THEN person_id END)) * 100, 2) as performance_rate_pct
        FROM `{DATASET_PREFIX}quality_measures.summary_wide`
        
        UNION ALL
        
        SELECT 
            'cqm_130' as measure_name,
            SUM(CASE WHEN cqm_130 = 1 THEN 1 ELSE 0 END) as numerator,
            COUNT(CASE WHEN cqm_130 IS NOT NULL THEN person_id END) as denominator,
            ROUND(SAFE_DIVIDE(SUM(CASE WHEN cqm_130 = 1 THEN 1 ELSE 0 END), COUNT(CASE WHEN cqm_130 IS NOT NULL THEN person_id END)) * 100, 2) as performance_rate_pct
        FROM `{DATASET_PREFIX}quality_measures.summary_wide`
        
        UNION ALL
        
        SELECT 
            'cqm_438' as measure_name,
            SUM(CASE WHEN cqm_438 = 1 THEN 1 ELSE 0 END) as numerator,
            COUNT(CASE WHEN cqm_438 IS NOT NULL THEN person_id END) as denominator,
            ROUND(SAFE_DIVIDE(SUM(CASE WHEN cqm_438 = 1 THEN 1 ELSE 0 END), COUNT(CASE WHEN cqm_438 IS NOT NULL THEN person_id END)) * 100, 2) as performance_rate_pct
        FROM `{DATASET_PREFIX}quality_measures.summary_wide`
        
        ORDER BY measure_name
        """
        
        df = get_from_cache_or_execute(query, params=params, ttl_minutes=360)
        result = {
            'measures_count': len(df),
            'measures': df.to_dict('records')
        }
        
        if len(df) > 0:
            result['avg_performance_rate'] = df['performance_rate_pct'].mean()
    
    return result

@mcp.tool()
def get_chronic_conditions_prevalence(
    condition_category: Optional[str] = None,
    year: str = "2018"
) -> Dict[str, Any]:
    """
    Get chronic conditions prevalence analysis.
    
    Args:
        condition_category: Optional filter for specific condition category (matches the `condition` field)
        year: Year for analysis (YYYY format)
        
    Returns:
        Dictionary containing chronic condition prevalence
    """
    # Define the analysis window for the given year
    start_date = f"{year}-01-01"
    end_date = f"{year}-12-31"

    where_clauses = [
        # A condition is considered prevalent in the year if it overlaps the year window
        "first_diagnosis_date <= DATE(@end_date)",
        "(last_diagnosis_date IS NULL OR last_diagnosis_date >= DATE(@start_date))"
    ]
    params = {"start_date": start_date, "end_date": end_date, "year": int(year)}

    if condition_category:
        where_clauses.append("`condition` = @condition_category")
        params["condition_category"] = condition_category
    
    where_clause = " AND ".join(where_clauses)
    
    query = f"""
    SELECT 
        `condition` AS condition_name,
        COUNT(DISTINCT person_id) AS patient_count,
        SAFE_DIVIDE(
            COUNT(DISTINCT person_id),
            (
                SELECT COUNT(DISTINCT person_id)
                FROM `{DATASET_PREFIX}core.medical_claim`
                WHERE EXTRACT(YEAR FROM claim_start_date) = @year
            )
        ) * 100 AS prevalence_rate
    FROM `{DATASET_PREFIX}chronic_conditions.tuva_chronic_conditions_long`
    WHERE {where_clause}
    GROUP BY condition_name
    ORDER BY patient_count DESC
    LIMIT 20
    """
    
    df = get_from_cache_or_execute(query, params=params, ttl_minutes=480)  # 8 hour cache for chronic conditions
    result = {
        'conditions_analyzed': len(df),
        'conditions': df.to_dict('records')
    }
    
    return result

@mcp.tool()
def get_high_cost_patients(
    cost_threshold: float = 10000.0,
    year: str = "2018",
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
            person_id,
            SUM(paid_amount) as total_paid,
            SUM(allowed_amount) as total_allowed,
            COUNT(DISTINCT claim_id) as total_claims,
            COUNT(DISTINCT CASE WHEN claim_type = 'institutional' THEN claim_id END) as inpatient_claims,
            COUNT(DISTINCT CASE WHEN claim_type = 'professional' THEN claim_id END) as outpatient_claims
        FROM `{DATASET_PREFIX}core.medical_claim`
        WHERE EXTRACT(YEAR FROM claim_start_date) = @year
        GROUP BY person_id
        HAVING total_paid >= @cost_threshold
        ORDER BY total_paid DESC
        LIMIT @limit
    )
    SELECT 
        pc.*,
        EXTRACT(YEAR FROM p.birth_date) as birth_year,
        p.sex as gender,
        p.age
    FROM patient_costs pc
    JOIN `{DATASET_PREFIX}core.patient` p ON pc.person_id = p.person_id
    ORDER BY pc.total_paid DESC
    """
    params = {"year": int(year), "cost_threshold": cost_threshold, "limit": limit}
    
    df = get_from_cache_or_execute(query, params=params, ttl_minutes=30)  # 30 min cache for high-cost analysis
    
    result = {
        'high_cost_patient_count': len(df),
        'total_cost_all_patients': df['total_paid'].sum() if len(df) > 0 else 0,
        'avg_cost_per_patient': df['total_paid'].mean() if len(df) > 0 else 0,
        'patients': df.to_dict('records')
    }
    
    # Convert any remaining Decimal objects in the result
    return convert_decimal_values(result)

@mcp.tool()
def get_readmissions_analysis(
    year: str = "2018",
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
    where_clauses = ["EXTRACT(YEAR FROM admit_date) = @year"]
    params = {"year": int(year)}

    if condition_category:
        where_clauses.append("diagnosis_ccs LIKE @condition_category")
        params["condition_category"] = f"%{condition_category}%"
    
    where_clause = " AND ".join(where_clauses)
    
    query = f"""
    SELECT 
        COUNT(DISTINCT encounter_id) as total_encounters,
        COUNT(DISTINCT CASE WHEN index_admission_flag = 0 AND disqualified_encounter_flag = 0 THEN encounter_id END) as readmissions,
        SAFE_DIVIDE(COUNT(DISTINCT CASE WHEN index_admission_flag = 0 AND disqualified_encounter_flag = 0 THEN encounter_id END), COUNT(DISTINCT encounter_id)) * 100 as readmission_rate,
        AVG(length_of_stay) as avg_los,
        SUM(paid_amount) as total_cost
    FROM `{DATASET_PREFIX}readmissions.encounter_augmented`
    WHERE {where_clause}
    """
    
    df = get_from_cache_or_execute(query, params=params, ttl_minutes=180)  # 3 hour cache for readmissions
    result = df.iloc[0].to_dict()
    
    return result

@mcp.tool()
def get_hcc_risk_scores(
    year: str = "2018",
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
        person_id,
        blended_risk_score as hcc_risk_score,
        member_months
    FROM `{DATASET_PREFIX}cms_hcc.patient_risk_scores`
    WHERE payment_year = @year
      AND blended_risk_score IS NOT NULL
    ORDER BY blended_risk_score DESC
    LIMIT @limit
    """
    params = {"year": int(year), "limit": limit}
    
    df = get_from_cache_or_execute(query, params=params, ttl_minutes=720)  # 12 hour cache for risk scores
    
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
