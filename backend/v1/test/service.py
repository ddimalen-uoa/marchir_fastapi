import logger
from fastapi import UploadFile, HTTPException
from uuid import UUID, uuid4
from sqlalchemy.orm import Session
from sqlalchemy import select, func, distinct
from math import ceil

from v1.test import model as test_models
from . import schema

def get_test_module(
    db: Session    
):
    data = db.query(test_models.TestTable).all()

    return data

def add_test(
        db: Session, 
        add_test_request: schema.AddTestRequest,
    ) -> test_models.TestTable:
    try:
        create_test_model = test_models.TestTable(
            name = add_test_request.name,
            value = add_test_request.value
        )
        db.add(create_test_model)
        db.commit()

        db.refresh(create_test_model)

        return create_test_model
        
    except Exception as e:
        logger.logging.error(
            f"Failed to add item: {add_test_request.name}. Error: {str(e)}"
        )
        db.rollback()
        raise