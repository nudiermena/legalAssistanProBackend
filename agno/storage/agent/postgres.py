from typing import Dict, Any, Optional
from datetime import datetime
import json
from sqlalchemy import create_engine, Column, Integer, String, JSON, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class AgentInteraction(Base):
    __tablename__ = 'agent_interactions'
    
    id = Column(Integer, primary_key=True)
    agent_name = Column(String)
    prompt = Column(String)
    response = Column(String)
    metadata = Column(JSON)
    timestamp = Column(DateTime, default=datetime.utcnow)

class PostgresAgentStorage:
    def __init__(self, connection_string: str):
        self.engine = create_engine(connection_string)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
    
    def store(self, data: Dict[str, Any]) -> None:
        """
        Store an agent interaction in the database
        """
        session = self.Session()
        try:
            interaction = AgentInteraction(
                agent_name=data.get('agent_name', 'unknown'),
                prompt=data.get('prompt', ''),
                response=data.get('response', ''),
                metadata=data.get('metadata', {}),
                timestamp=datetime.fromisoformat(data.get('timestamp', datetime.utcnow().isoformat()))
            )
            session.add(interaction)
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def get_interactions(
        self,
        agent_name: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> list:
        """
        Retrieve agent interactions with optional filters
        """
        session = self.Session()
        try:
            query = session.query(AgentInteraction)
            
            if agent_name:
                query = query.filter(AgentInteraction.agent_name == agent_name)
            if start_date:
                query = query.filter(AgentInteraction.timestamp >= start_date)
            if end_date:
                query = query.filter(AgentInteraction.timestamp <= end_date)
            
            return query.order_by(AgentInteraction.timestamp.desc()).limit(limit).all()
        finally:
            session.close()
    
    def clear_interactions(self, agent_name: Optional[str] = None) -> None:
        """
        Clear all interactions for an agent or all agents
        """
        session = self.Session()
        try:
            query = session.query(AgentInteraction)
            if agent_name:
                query = query.filter(AgentInteraction.agent_name == agent_name)
            query.delete()
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close() 