# ============================================
# FILE:
# app/services/usage_service.py
# ============================================

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
    def get_summary():
        """Overall usage summary stats."""

        try:
            result = supabase.table(
                "chat_usage"
            ).select("*").execute()

            data = result.data
            total = len(data)

            if total == 0:
                return {
                    "total_messages": 0,
                    "unique_sessions": 0,
                    "avg_response_time_ms": 0,
                    "error_count": 0,
                    "success_rate": 0,
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

            return {
                "total_messages": total,
                "unique_sessions": sessions,
                "avg_response_time_ms": round(avg_time),
                "error_count": errors,
                "success_rate": round(
                    (total - errors) / total * 100, 1
                ),
            }

        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def get_recent(limit: int = 50):
        """Most recent usage logs."""

        try:
            result = supabase.table(
                "chat_usage"
            ).select("*").order(
                "created_at", desc=True
            ).limit(limit).execute()

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
