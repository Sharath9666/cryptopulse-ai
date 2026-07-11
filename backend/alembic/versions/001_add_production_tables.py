"""
Alembic migration script to create tables for production persistence.
Generated manually to avoid live DB connection.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "001_add_production_tables"
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        "prediction_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("prediction_id", sa.String(length=100), nullable=False, unique=True),
        sa.Column("symbol", sa.String(length=20), nullable=False),
        sa.Column("timeframe", sa.String(length=10), nullable=False),
        sa.Column("direction", sa.String(length=20), nullable=False),
        sa.Column("confidence", sa.String(length=20), nullable=False),
        sa.Column("predicted_move", sa.Float(), nullable=False),
        sa.Column("entry_price", sa.Float(), nullable=False),
        sa.Column("prediction_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("evaluation_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("actual_price", sa.Float(), nullable=True),
        sa.Column("actual_move", sa.Float(), nullable=True),
        sa.Column("correct", sa.Boolean(), nullable=True),
    )
    op.create_index(op.f("ix_prediction_records_prediction_id"), "prediction_records", ["prediction_id"], unique=True)

    op.create_table(
        "trade_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("trade_id", sa.String(length=100), nullable=False, unique=True),
        sa.Column("symbol", sa.String(length=20), nullable=False),
        sa.Column("direction", sa.String(length=20), nullable=False, default="LONG"),
        sa.Column("entry_price", sa.Float(), nullable=False),
        sa.Column("exit_price", sa.Float(), nullable=True),
        sa.Column("quantity", sa.Float(), nullable=False),
        sa.Column("profit_loss", sa.Float(), nullable=False, default=0.0),
        sa.Column("status", sa.String(length=20), nullable=False, default="OPEN"),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(op.f("ix_trade_records_trade_id"), "trade_records", ["trade_id"], unique=True)

    op.create_table(
        "backtest_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("backtest_id", sa.String(length=100), nullable=False, unique=True),
        sa.Column("symbol", sa.String(length=20), nullable=False),
        sa.Column("timeframe", sa.String(length=10), nullable=False),
        sa.Column("total_trades", sa.Integer(), nullable=False, default=0),
        sa.Column("winning_trades", sa.Integer(), nullable=False, default=0),
        sa.Column("losing_trades", sa.Integer(), nullable=False, default=0),
        sa.Column("win_rate", sa.Float(), nullable=False, default=0.0),
        sa.Column("total_profit", sa.Float(), nullable=False, default=0.0),
        sa.Column("profit_percentage", sa.Float(), nullable=False, default=0.0),
        sa.Column("maximum_drawdown", sa.Float(), nullable=False, default=0.0),
        sa.Column("average_trade_return", sa.Float(), nullable=False, default=0.0),
    )
    op.create_index(op.f("ix_backtest_results_backtest_id"), "backtest_results", ["backtest_id"], unique=True)

    op.create_table(
        "market_candles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("symbol", sa.String(length=20), nullable=False),
        sa.Column("timeframe", sa.String(length=10), nullable=False),
        sa.Column("open", sa.Float(), nullable=False),
        sa.Column("high", sa.Float(), nullable=False),
        sa.Column("low", sa.Float(), nullable=False),
        sa.Column("close", sa.Float(), nullable=False),
        sa.Column("volume", sa.Float(), nullable=False),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(op.f("ix_market_candles_symbol_timeframe"), "market_candles", ["symbol", "timeframe"])

    op.create_table(
        "portfolio_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("starting_balance", sa.Float(), nullable=False),
        sa.Column("available_balance", sa.Float(), nullable=False),
        sa.Column("total_profit", sa.Float(), nullable=False),
        sa.Column("total_loss", sa.Float(), nullable=False),
        sa.Column("open_positions_count", sa.Integer(), nullable=False),
        sa.Column("closed_trades_count", sa.Integer(), nullable=False),
    )

def downgrade() -> None:
    op.drop_table("portfolio_snapshots")
    op.drop_index(op.f("ix_market_candles_symbol_timeframe"), table_name="market_candles")
    op.drop_table("market_candles")
    op.drop_table("backtest_results")
    op.drop_index(op.f("ix_trade_records_trade_id"), table_name="trade_records")
    op.drop_table("trade_records")
    op.drop_index(op.f("ix_prediction_records_prediction_id"), table_name="prediction_records")
    op.drop_table("prediction_records")
