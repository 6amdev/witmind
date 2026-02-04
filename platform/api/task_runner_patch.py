# Lines 518-525 เปลี่ยนจาก:
#         else:
#             await self.add_activity(...)
# เป็น:
#         else:
#             await self.update_task_status(task_id, "planned")
#             await self.add_activity(... + ". Task reset to planned.")
#             logger.warning(...)
