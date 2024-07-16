from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


# TODO: validate
class Policy(Base):

    __tablename__ = "policy"

    policy_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    description = Column(String)
    input_schema = Column(String)
    repository = Column(String)
    job_name = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Run(Base):

    __tablename__ = "run"

    run_id = Column(Integer, primary_key=True)
    policy_id = Column(Integer, ForeignKey("policy.policy_id"))
    status = Column(String)
    result = Column(String, nullable=True)
    dagster_run_id = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_updated_at = Column(DateTime(timezone=True), onupdate=func.now())


if __name__ == "__main__":
    engine = create_engine("sqlite:///server/example.db", echo=True)
    Base.metadata.create_all(engine)
