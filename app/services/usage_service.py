# ============================================
# FILE:
# app/services/usage_service.py
# ============================================

from datetime import datetime, timedelta
from app.db.supabase import supabase


class UsageTracker:
    """Logs and queries chatbot usage from Supabase."""

    @staticmethod
    def log(
        session_id: str,
        ip_address: str,
        user_message: str,
        response_length: int,
        response_time_ms: int,
        agent: str = "resume",
        status: str = "success",
        error_message: str = None,
        input_tokens: int = 0,
        output_tokens: int = 0,
    ):
        try:
            data = {
                "session_id": session_id,
                "ip_address": ip_address,
                "user_message": user_message,
                "response_length": response_length,
                "response_time_ms": response_time_ms,
                "agent": agent,
                "status": status,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
            }

            if error_message:
                data["error_message"] = error_message

            supabase.table(
                "chat_usage"
            ).insert(data).execute()

        except Exception as e:
            print(f"[UsageTracker] log error: {e}")

    # ========================================
    # ANALYTICS QUERIES
    # ========================================

    @staticmethod
    def get_summary(days: int = None):
        """Overall usage summary stats, optionally filtered by days."""

        try:
            query = supabase.table("chat_usage").select("*")
            if days is not None:
                cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
                query = query.gte("created_at", cutoff)
            
            result = query.execute()

            data = result.data
            total = len(data)

            if total == 0:
                return {
                    "total_messages": 0,
                    "unique_sessions": 0,
                    "avg_response_time_ms": 0,
                    "error_count": 0,
                    "success_rate": 0,
                    "total_input_tokens": 0,
                    "total_output_tokens": 0,
                }

            sessions = len(set(
                d["session_id"]
                for d in data
                if d.get("session_id")
            ))

            avg_time = sum(
                d.get("response_time_ms", 0)
                for d in data
            ) / total

            errors = sum(
                1 for d in data
                if d.get("status") == "error"
            )

            total_input = sum(d.get("input_tokens") or 0 for d in data)
            total_output = sum(d.get("output_tokens") or 0 for d in data)

            return {
                "total_messages": total,
                "unique_sessions": sessions,
                "avg_response_time_ms": round(avg_time),
                "error_count": errors,
                "success_rate": round(
                    (total - errors) / total * 100, 1
                ),
                "total_input_tokens": total_input,
                "total_output_tokens": total_output,
            }

        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def get_recent(limit: int = 50, days: int = None, offset: int = 0):
        """Most recent usage logs, optionally filtered by days and paginated."""

        try:
            query = supabase.table("chat_usage").select("*").order(
                "created_at", desc=True
            ).range(offset, offset + limit - 1)
            
            if days is not None:
                cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
                query = query.gte("created_at", cutoff)

            result = query.execute()

            return result.data

        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def get_daily_stats(days: int = 30):
        """Daily aggregated usage counts."""

        try:
            result = supabase.table(
                "chat_usage"
            ).select("*").order(
                "created_at", desc=True
            ).execute()

            data = result.data
            daily = {}

            for d in data:
                date = d["created_at"][:10]

                if date not in daily:
                    daily[date] = {
                        "date": date,
                        "count": 0,
                        "errors": 0,
                        "avg_response_ms": 0,
                        "_total_ms": 0,
                    }

                daily[date]["count"] += 1
                daily[date]["_total_ms"] += d.get(
                    "response_time_ms", 0
                )

                if d.get("status") == "error":
                    daily[date]["errors"] += 1

            # Calculate averages
            for day in daily.values():
                if day["count"] > 0:
                    day["avg_response_ms"] = round(
                        day["_total_ms"] / day["count"]
                    )
                del day["_total_ms"]

            sorted_days = sorted(
                daily.values(),
                key=lambda x: x["date"],
                reverse=True,
            )

            return sorted_days[:days]

        except Exception as e:
            return {"error": str(e)}
