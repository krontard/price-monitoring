from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from app.schemas.monitoring import (
    MonitoringRequest,
    MonitoringResponse,
    TaskResultResponse, 
    MarketplaceRequest,
    MarketplaceResponse,
    TaskListResponse,
    TestTaskResponse
)

from celery.price_monitoring import (
    test_task,
    monitor_product_prices, 
    monitor_all_products,
    parse_amazon_price,
    parse_wildberries_price,
    parse_ozon_price
)

from app.models.task_history import TaskHistory
from app.database import get_db

router = APIRouter()

@router.post("/start", response_model=MonitoringResponse)
async def start_monitoring(request: MonitoringRequest, db: Session = Depends(get_db)):
    try:
        product_id = request.product_id or hash(request.product_name) % 10000
        task = monitor_product_prices.delay(request.product_name, product_id)

        db_task = TaskHistory(
            task_id=task.id,
            product_name=request.product_name,
            product_id=product_id,
            status="started"
        )
        db.add(db_task)
        db.commit()
        db.refresh(db_task)
        
        return MonitoringResponse(
            task_id=task.id,
            message=f"Мониторинг цен для {request.product_name} запущен",
            product_name=request.product_name,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при запуске мониторинга: {str(e)}")

@router.get("/result/{task_id}", response_model=TaskResultResponse)
async def get_result(task_id: str, db: Session = Depends(get_db)):
    try:
        from celery.result import AsyncResult
        from celery.app import celery_app

        result = AsyncResult(task_id, app=celery_app)
        
        # Получаем задачу из базы данных
        db_task = db.query(TaskHistory).filter(TaskHistory.task_id == task_id).first()
        if not db_task:
            raise HTTPException(status_code=404, detail="Задача не найдена")

        # Обновляем статус в базе данных
        if result.state == "PENDING":
            db_task.status = "pending"
        elif result.status == "SUCCESS":
            db_task.status = "completed"
            db_task.completed_at = datetime.now()
            if result.result:
                db_task.result_data = str(result.result)
        elif result.status == "FAILURE":
            db_task.status = "failed"
            db_task.completed_at = datetime.now()
            db_task.error_message = str(result.result)
        else:
            db_task.status = result.state.lower()
            
        db.commit()

        return TaskResultResponse(
            task_id=task_id, 
            status=db_task.status, 
            error=db_task.error_message
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при получении результата: {str(e)}")


@router.get("/tasks", response_model=TaskListResponse)
async def get_all_tasks(db: Session = Depends(get_db)):
    try:
        active_tasks = db.query(TaskHistory).filter(
            TaskHistory.status.in_(["started", "pending", "running"])
        ).order_by(TaskHistory.started_at.desc()).all()
        
        tasks_data = []
        for task in active_tasks:
            tasks_data.append({
                "task_id": task.task_id,
                "product_name": task.product_name,
                "product_id": task.product_id,
                "status": task.status,
                "started_at": task.started_at.isoformat()
            })
        
        return TaskListResponse(
            tasks=tasks_data,
            total_count=len(tasks_data)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при получении списка задач: {str(e)}")


@router.post("/stop/{task_id}")
async def stop_task(task_id: str, db: Session = Depends(get_db)):
    try:
        from celery.result import AsyncResult
        from celery.app import celery_app
        
        # Получаем задачу из базы данных
        db_task = db.query(TaskHistory).filter(TaskHistory.task_id == task_id).first()
        if not db_task:
            raise HTTPException(status_code=404, detail="Задача не найдена")
        
        # Останавливаем задачу в Celery
        result = AsyncResult(task_id, app=celery_app)
        result.revoke(terminate=True)
        
        # Обновляем статус в базе данных
        db_task.status = "stopped"
        db_task.completed_at = datetime.now()
        db.commit()
            
        return {
            "message": f"Задача {task_id} остановлена", 
            "task_id": task_id,
            "product_name": db_task.product_name
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при остановке задачи: {str(e)}")


@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    try:
        from celery.app import celery_app
        
        # Проверяем подключение к Celery
        celery_status = "ok"
        try:
            celery_app.control.inspect().active()
        except Exception:
            celery_status = "error"
        
        # Считаем активные задачи из базы данных
        active_count = db.query(TaskHistory).filter(
            TaskHistory.status.in_(["started", "pending", "running"])
        ).count()
            
        return {
            "status": "healthy" if celery_status == "ok" else "unhealthy",
            "celery": celery_status,
            "active_tasks_count": active_count,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при проверке здоровья: {str(e)}")

