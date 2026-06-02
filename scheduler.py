"""
定时任务调度器
用于定期清理过期的历史记录
"""
import logging
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)


def setup_scheduler(app):
    """设置定时任务"""
    scheduler = BackgroundScheduler()

    # 每天凌晨3点清理过期对话
    scheduler.add_job(
        func=cleanup_old_conversations,
        trigger=IntervalTrigger(days=1),
        args=[app],
        id='cleanup_conversations',
        name='清理过期对话',
        replace_existing=True
    )

    scheduler.start()
    logger.info("定时任务调度器已启动")

    # 关闭时停止调度器
    import atexit
    atexit.register(lambda: scheduler.shutdown())

    return scheduler


def cleanup_old_conversations(app):
    """清理过期的对话记录"""
    with app.app_context():
        from models import db, Conversation
        from config import Config

        retention_days = Config.HISTORY_RETENTION_DAYS
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)

        try:
            old_conversations = Conversation.query.filter(
                Conversation.updated_at < cutoff_date
            ).all()

            count = len(old_conversations)
            for conv in old_conversations:
                db.session.delete(conv)

            db.session.commit()

            if count > 0:
                logger.info(f"已清理 {count} 个超过 {retention_days} 天的对话")
            else:
                logger.debug("没有需要清理的过期对话")

        except Exception as e:
            logger.error(f"清理对话失败: {str(e)}")
            db.session.rollback()
