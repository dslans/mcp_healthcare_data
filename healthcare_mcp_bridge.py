#!/usr/bin/env python3
"""
Healthcare MCP Bridge for Warp

This creates a proper MCP server that bridges to the Cloud Run HTTP API,
allowing Warp to use the healthcare analytics tools through the MCP protocol.

Usage:
    python healthcare_mcp_bridge.py

Or with FastMCP:
    fastmcp run healthcare_mcp_bridge.py

Configure in your MCP client:
{
  "mcpServers": {
    "healthcare-analytics": {
      "command": "python",
      "args": ["/path/to/healthcare_mcp_bridge.py"],
      "env": {
        "CLOUD_RUN_URL": "https://healthcare-mcp-server-842907846470.us-central1.run.app"
      }
    }
  }
}
"""

import asyncio
import json
import os
from typing import Any, Dict, Optional
import httpx
from fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("Healthcare Analytics Bridge")

# Cloud Run service URL
CLOUD_RUN_URL = os.getenv("CLOUD_RUN_URL", "https://healthcare-mcp-server-842907846470.us-central1.run.app")

async def call_api(endpoint: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
    """Call the Cloud Run HTTP API endpoint"""
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            if data:
                response = await client.post(f"{CLOUD_RUN_URL}/{endpoint}", json=data)
            else:
                response = await client.get(f"{CLOUD_RUN_URL}/{endpoint}")
            
            response.raise_for_status()
            return response.json()
    except httpx.RequestError as e:
        raise Exception(f"API request failed: {str(e)}")
    except httpx.HTTPStatusError as e:
        raise Exception(f"API returned error {e.response.status_code}: {e.response.text}")

@mcp.tool()
async def get_patient_demographics(
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
    data = {
        "start_date": start_date,
        "end_date": end_date,
        "age_groups": age_groups
    }
    return await call_api("analytics/demographics", data)

@mcp.tool()
async def get_utilization_summary(
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
    data = {
        "start_date": start_date,
        "end_date": end_date,
        "service_category": service_category
    }
    return await call_api("analytics/utilization", data)

@mcp.tool()
async def get_pmpm_analysis(
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
    data = {
        "start_date": start_date,
        "end_date": end_date,
        "payer": payer
    }
    return await call_api("analytics/pmpm", data)

@mcp.tool()
async def get_quality_measures_summary(
    measure_name: Optional[str] = None,
    year: str = "2018"
) -> Dict[str, Any]:
    """
    Get quality measures summary for the specified year.
    
    Args:
        measure_name: Optional filter for specific measure
        year: Year for analysis (YYYY format)
        
    Returns:
        Dictionary containing quality measure results
    """
    data = {
        "measure_name": measure_name,
        "year": year
    }
    return await call_api("analytics/quality-measures", data)

@mcp.tool()
async def get_chronic_conditions_prevalence(
    condition_category: Optional[str] = None,
    year: str = "2018"
) -> Dict[str, Any]:
    """
    Get chronic conditions prevalence analysis.
    
    Args:
        condition_category: Optional filter for specific condition category
        year: Year for analysis (YYYY format)
        
    Returns:
        Dictionary containing chronic condition prevalence
    """
    data = {
        "condition_category": condition_category,
        "year": year
    }
    return await call_api("analytics/chronic-conditions", data)

@mcp.tool()
async def get_high_cost_patients(
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
    data = {
        "cost_threshold": cost_threshold,
        "year": year,
        "limit": limit
    }
    return await call_api("analytics/high-cost-patients", data)

@mcp.tool()
async def get_readmissions_analysis(
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
    data = {
        "year": year,
        "condition_category": condition_category
    }
    return await call_api("analytics/readmissions", data)

@mcp.tool()
async def get_hcc_risk_scores(
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
    data = {
        "year": year,
        "limit": limit
    }
    return await call_api("analytics/hcc-risk-scores", data)

@mcp.tool()
async def get_service_info() -> Dict[str, Any]:
    """
    Get API information and available endpoints.
    
    Returns:
        Dictionary containing service information and available endpoints
    """
    return await call_api("api/info")

@mcp.tool()
async def health_check() -> Dict[str, Any]:
    """
    Check the health status of the healthcare analytics service.
    
    Returns:
        Dictionary containing health status and service information
    """
    return await call_api("health")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        # Test mode - run a simple health check
        async def test():
            print("Testing healthcare MCP bridge...")
            try:
                result = await health_check()
                print(f"✅ Health check passed: {result}")
            except Exception as e:
                print(f"❌ Health check failed: {e}")
        
        asyncio.run(test())
    else:
        mcp.run()
