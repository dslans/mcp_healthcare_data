#!/usr/bin/env python3
"""
Cloud Run HTTP Server for Healthcare MCP Server

This creates an HTTP wrapper around the FastMCP server for Cloud Run deployment.
It provides both HTTP endpoints and MCP protocol support.
"""

import os
import asyncio
import json
from typing import Dict, Any
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import logging

# Import our healthcare MCP server
import healthcare_mcp_server

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Healthcare Analytics MCP Server",
    description="Healthcare data analysis tools via HTTP and MCP protocols",
    version="1.0.0"
)

# Request models
class AnalysisRequest(BaseModel):
    start_date: str = "2018-01-01"
    end_date: str = "2018-12-31"
    
class DemographicsRequest(AnalysisRequest):
    age_groups: bool = True
    
class UtilizationRequest(AnalysisRequest):
    service_category: str = None
    
class PMPMRequest(AnalysisRequest):
    payer: str = None

class HighCostRequest(BaseModel):
    cost_threshold: float = 10000.0
    year: str = "2018"
    limit: int = 100

class YearRequest(BaseModel):
    year: str = "2018"
    
class HCCRequest(YearRequest):
    limit: int = 1000

class ConditionsRequest(YearRequest):
    condition_category: str = None

class QualityRequest(YearRequest):
    measure_name: str = None

class ReadmissionsRequest(YearRequest):
    condition_category: str = None

# Health check endpoint
@app.get("/")
@app.get("/health")
async def health_check():
    """Health check endpoint for Cloud Run"""
    try:
        # Test BigQuery connection
        test_result = healthcare_mcp_server.get_patient_demographics(
            start_date="2018-01-01", 
            end_date="2018-01-01", 
            age_groups=False
        )
        return {
            "status": "healthy",
            "service": "Healthcare MCP Server",
            "bigquery_connection": "ok",
            "total_patients": test_result.get("total_patients", 0)
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")

# Analytics endpoints
@app.post("/analytics/demographics")
async def get_demographics(request: DemographicsRequest):
    """Get patient demographics analysis"""
    try:
        result = healthcare_mcp_server.get_patient_demographics(
            start_date=request.start_date,
            end_date=request.end_date,
            age_groups=request.age_groups
        )
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"Demographics analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analytics/utilization")
async def get_utilization(request: UtilizationRequest):
    """Get healthcare utilization summary"""
    try:
        result = healthcare_mcp_server.get_utilization_summary(
            start_date=request.start_date,
            end_date=request.end_date,
            service_category=request.service_category
        )
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"Utilization analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analytics/pmpm")
async def get_pmpm(request: PMPMRequest):
    """Get PMPM financial analysis"""
    try:
        result = healthcare_mcp_server.get_pmpm_analysis(
            start_date=request.start_date,
            end_date=request.end_date,
            payer=request.payer
        )
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"PMPM analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analytics/quality-measures")
async def get_quality_measures(request: QualityRequest):
    """Get quality measures summary"""
    try:
        result = healthcare_mcp_server.get_quality_measures_summary(
            measure_name=request.measure_name,
            year=request.year
        )
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"Quality measures analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analytics/chronic-conditions")
async def get_chronic_conditions(request: ConditionsRequest):
    """Get chronic conditions prevalence"""
    try:
        result = healthcare_mcp_server.get_chronic_conditions_prevalence(
            condition_category=request.condition_category,
            year=request.year
        )
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"Chronic conditions analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analytics/high-cost-patients")
async def get_high_cost_patients(request: HighCostRequest):
    """Get high-cost patients for case management"""
    try:
        result = healthcare_mcp_server.get_high_cost_patients(
            cost_threshold=request.cost_threshold,
            year=request.year,
            limit=request.limit
        )
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"High-cost patients analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analytics/readmissions")
async def get_readmissions(request: ReadmissionsRequest):
    """Get readmissions analysis"""
    try:
        result = healthcare_mcp_server.get_readmissions_analysis(
            year=request.year,
            condition_category=request.condition_category
        )
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"Readmissions analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analytics/hcc-risk-scores")
async def get_hcc_risk_scores(request: HCCRequest):
    """Get HCC risk scores analysis"""
    try:
        result = healthcare_mcp_server.get_hcc_risk_scores(
            year=request.year,
            limit=request.limit
        )
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"HCC risk scores analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# API documentation endpoint
@app.get("/api/info")
async def api_info():
    """Get API information and available endpoints"""
    return {
        "service": "Healthcare Analytics MCP Server",
        "version": "1.0.0",
        "endpoints": {
            "health": "GET /health - Service health check",
            "demographics": "POST /analytics/demographics - Patient demographics analysis",
            "utilization": "POST /analytics/utilization - Healthcare utilization summary", 
            "pmpm": "POST /analytics/pmpm - PMPM financial analysis",
            "quality_measures": "POST /analytics/quality-measures - Quality measures summary",
            "chronic_conditions": "POST /analytics/chronic-conditions - Chronic conditions prevalence",
            "high_cost_patients": "POST /analytics/high-cost-patients - High-cost patient identification",
            "readmissions": "POST /analytics/readmissions - Readmissions analysis",
            "hcc_risk_scores": "POST /analytics/hcc-risk-scores - HCC risk scores analysis"
        },
        "data_source": "Tuva Health BigQuery dataset",
        "authentication": "Google Cloud ADC"
    }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    logger.info(f"Starting Healthcare MCP Server on port {port}")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
