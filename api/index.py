from http.server import BaseHTTPRequestHandler
import json
import urllib.parse
from datetime import datetime
import sys
import os

# Add parent directory to system path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database
import sync_engine

class handler(BaseHTTPRequestHandler):

    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def send_json(self, response_data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response_data).encode('utf-8'))

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        conn = database.get_db()
        cursor = conn.cursor()

        try:
            if path == "/api/vessels" or path.endswith("/api/vessels"):
                cursor.execute("SELECT * FROM vessels")
                rows = [dict(r) for r in cursor.fetchall()]
                return self.send_json({"success": True, "vessels": rows})

            elif path == "/api/chassis" or path.endswith("/api/chassis"):
                vessel_id = query.get("vessel_id", [None])[0]
                if vessel_id:
                    cursor.execute("SELECT * FROM chassis WHERE vessel_id = ?", (vessel_id,))
                else:
                    cursor.execute("SELECT * FROM chassis")
                rows = [dict(r) for r in cursor.fetchall()]
                return self.send_json({"success": True, "chassis": rows})

            elif "/api/chassis/search" in path:
                q = query.get("query", [""])[0].strip()
                if not q:
                    return self.send_json({"success": True, "chassis": []})
                
                cursor.execute("""
                    SELECT c.*, v.name as vessel_name, v.voyage 
                    FROM chassis c 
                    JOIN vessels v ON c.vessel_id = v.id 
                    WHERE c.last_6 LIKE ? OR c.vin LIKE ?
                """, (f"%{q}%", f"%{q}%"))
                rows = [dict(r) for r in cursor.fetchall()]
                return self.send_json({"success": True, "chassis": rows})

            elif "/api/tally/" in path:
                vin = path.split("/api/tally/")[-1].strip()
                cursor.execute("SELECT * FROM tally_sheets WHERE vin = ?", (vin,))
                row = cursor.fetchone()

                cursor.execute("""
                    SELECT c.*, v.name as vessel_name, v.voyage 
                    FROM chassis c 
                    JOIN vessels v ON c.vessel_id = v.id 
                    WHERE c.vin = ?
                """, (vin,))
                chassis_row = cursor.fetchone()

                cursor.execute("SELECT * FROM security_checks WHERE vin = ?", (vin,))
                sec_row = cursor.fetchone()

                cursor.execute("SELECT * FROM audit_trail WHERE vin = ? ORDER BY id ASC", (vin,))
                audit_rows = [dict(r) for r in cursor.fetchall()]

                cursor.execute("SELECT * FROM update_approvals WHERE vin = ? ORDER BY id DESC LIMIT 1", (vin,))
                approval_row = cursor.fetchone()

                if not chassis_row:
                    return self.send_json({"success": False, "message": "VIN not found in system"}, 404)

                chassis_dict = dict(chassis_row)
                tally_dict = dict(row) if row else None
                if tally_dict:
                    tally_dict["accessories_json"] = json.loads(tally_dict["accessories_json"] or "{}")
                    tally_dict["damages_json"] = json.loads(tally_dict["damages_json"] or "[]")
                    tally_dict["photos_json"] = json.loads(tally_dict["photos_json"] or "[]")

                sec_dict = dict(sec_row) if sec_row else None
                if sec_dict:
                    sec_dict["discrepancies_json"] = json.loads(sec_dict["discrepancies_json"] or "[]")

                return self.send_json({
                    "success": True,
                    "chassis": chassis_dict,
                    "tally": tally_dict,
                    "security": sec_dict,
                    "audit": audit_rows,
                    "latest_approval": dict(approval_row) if approval_row else None
                })

            elif path.endswith("/api/update-approval/list"):
                cursor.execute("""
                    SELECT a.*, c.model, c.vessel_id 
                    FROM update_approvals a 
                    JOIN chassis c ON a.vin = c.vin 
                    WHERE a.status = 'PENDING'
                """)
                rows = [dict(r) for r in cursor.fetchall()]
                return self.send_json({"success": True, "approvals": rows})

            elif path.endswith("/api/users"):
                cursor.execute("SELECT id, username, name, role, status, created_at FROM users ORDER BY id ASC")
                rows = [dict(r) for r in cursor.fetchall()]
                return self.send_json({"success": True, "users": rows})

            elif path.endswith("/api/admin/audit-logs"):
                cursor.execute("SELECT * FROM audit_trail ORDER BY id DESC LIMIT 100")
                rows = [dict(r) for r in cursor.fetchall()]
                return self.send_json({"success": True, "audit_logs": rows})

            elif path.endswith("/api/sync/status"):
                cursor.execute("SELECT status, COUNT(*) as count FROM sync_outbox GROUP BY status")
                counts = {r["status"]: r["count"] for r in cursor.fetchall()}
                cursor.execute("SELECT * FROM sync_outbox ORDER BY id DESC LIMIT 20")
                recent = [dict(r) for r in cursor.fetchall()]
                return self.send_json({"success": True, "outbox_counts": counts, "recent_events": recent})

            else:
                return self.send_json({"success": False, "message": f"Unknown API endpoint: {path}"}, 404)

        finally:
            conn.close()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8') if content_length > 0 else ""
        try:
            data = json.loads(body) if body else {}
        except Exception:
            data = {}

        conn = database.get_db()
        cursor = conn.cursor()
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        try:
            if path.endswith("/api/login"):
                username = data.get("username", "").strip()
                password = data.get("password", "").strip()
                cursor.execute("SELECT * FROM users WHERE username = ? AND password = ? AND status = 'ACTIVE'", (username, password))
                user = cursor.fetchone()
                if user:
                    user_dict = dict(user)
                    del user_dict["password"]
                    return self.send_json({"success": True, "user": user_dict})
                else:
                    return self.send_json({"success": False, "message": "Invalid username or password"}, 401)

            elif path.endswith("/api/sync/trigger"):
                res = sync_engine.process_outbox_queue()
                return self.send_json({"success": True, "sync_result": res})

            elif path.endswith("/api/external/manifest"):
                res = sync_engine.import_vessel_manifest(data)
                return self.send_json(res)

            elif path.endswith("/api/users"):
                username = data.get("username", "").strip()
                name = data.get("name", "").strip()
                role = data.get("role", "Surveyor").strip()
                password = data.get("password", "pass123").strip()

                if not username or not name:
                    return self.send_json({"success": False, "message": "Username and Name are required"}, 400)

                cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
                existing = cursor.fetchone()

                if existing:
                    cursor.execute("UPDATE users SET name = ?, role = ?, password = ? WHERE username = ?", (name, role, password, username))
                    msg = f"User '{username}' updated successfully."
                else:
                    cursor.execute("INSERT INTO users (username, name, role, password, status, created_at) VALUES (?,?,?,?,'ACTIVE',?)", (username, name, role, password, now_str))
                    msg = f"New user '{username}' created successfully."

                conn.commit()
                return self.send_json({"success": True, "message": msg})

            elif path.endswith("/api/tally"):
                vin = data.get("vin")
                doc_ref = data.get("doc_ref", "20586")
                vessel_id = data.get("vessel_id")
                tally_type = data.get("tally_type", "ONBOARD")
                status = data.get("status", "Confirmed")
                accessories = json.dumps(data.get("accessories", {}))
                damages = json.dumps(data.get("damages", []))
                photos = json.dumps(data.get("photos", []))
                remarks = data.get("remarks", "")
                user_id = data.get("user_id", "Surveyor 298")

                cursor.execute("SELECT id FROM tally_sheets WHERE vin = ?", (vin,))
                existing = cursor.fetchone()

                if existing:
                    cursor.execute("""
                        UPDATE tally_sheets 
                        SET status = ?, accessories_json = ?, damages_json = ?, photos_json = ?, remarks = ?, confirmed_by = ?, confirmed_at = ?
                        WHERE vin = ?
                    """, (status, accessories, damages, photos, remarks, user_id, now_str, vin))
                else:
                    cursor.execute("""
                        INSERT INTO tally_sheets (vin, doc_ref, vessel_id, tally_type, status, accessories_json, damages_json, photos_json, remarks, created_by, created_at, confirmed_by, confirmed_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (vin, doc_ref, vessel_id, tally_type, status, accessories, damages, photos, remarks, user_id, now_str, user_id, now_str))

                chassis_status = "Confirmed" if status == "Confirmed" else "In Progress"
                cursor.execute("UPDATE chassis SET tally_status = ? WHERE vin = ?", (chassis_status, vin))

                cursor.execute("""
                    INSERT INTO audit_trail (vin, work_point, user_id, user_role, timestamp, details)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (vin, "Onboard" if tally_type == "ONBOARD" else "Yard Update", user_id, "Surveyor", now_str, f"Tally Sheet {status} (Doc Ref: {doc_ref})"))

                cursor.execute("UPDATE update_approvals SET status = 'COMPLETED' WHERE vin = ? AND status = 'APPROVED'", (vin,))

                database.queue_sync_event(cursor, "TALLY_CONFIRMED", vin, {
                    "vin": vin,
                    "doc_ref": doc_ref,
                    "vessel_id": vessel_id,
                    "status": status,
                    "accessories": data.get("accessories", {}),
                    "damages": data.get("damages", []),
                    "remarks": remarks,
                    "user_id": user_id,
                    "timestamp": now_str
                })

                conn.commit()
                return self.send_json({"success": True, "message": f"Tally Sheet {status} successfully", "vin": vin})

            elif path.endswith("/api/admin/override-tally"):
                vin = data.get("vin")
                action = data.get("action", "UNLOCK")
                admin_id = data.get("admin_id", "System Administrator")

                if action == "UNLOCK":
                    cursor.execute("UPDATE chassis SET tally_status = 'In Progress' WHERE vin = ?", (vin,))
                    cursor.execute("UPDATE tally_sheets SET status = 'Draft' WHERE vin = ?", (vin,))
                    cursor.execute("""
                        INSERT INTO audit_trail (vin, work_point, user_id, user_role, timestamp, details)
                        VALUES (?, 'Admin Override', ?, 'Admin', ?, 'ADMIN FORCE UNLOCKED TALLY SHEET FOR EDITING')
                    """, (vin, admin_id, now_str))
                    conn.commit()
                    return self.send_json({"success": True, "message": f"Tally Sheet for VIN {vin} force unlocked by Admin."})

                elif action == "DELETE":
                    cursor.execute("DELETE FROM tally_sheets WHERE vin = ?", (vin,))
                    cursor.execute("DELETE FROM security_checks WHERE vin = ?", (vin,))
                    cursor.execute("UPDATE chassis SET tally_status = 'No Tally' WHERE vin = ?", (vin,))
                    cursor.execute("""
                        INSERT INTO audit_trail (vin, work_point, user_id, user_role, timestamp, details)
                        VALUES (?, 'Admin Delete', ?, 'Admin', ?, 'ADMIN PURGED TALLY SHEET RECORD')
                    """, (vin, admin_id, now_str))
                    conn.commit()
                    return self.send_json({"success": True, "message": f"Tally Sheet for VIN {vin} purged from database by Admin."})

            elif path.endswith("/api/admin/add-vessel"):
                v_id = data.get("id", f"VSL{datetime.now().strftime('%H%M%S')}")
                name = data.get("name", "").strip()
                voyage = data.get("voyage", "").strip()
                berth = data.get("berth_no", "Berth 1").strip()
                units = int(data.get("total_units", 100))
                arrival = datetime.now().strftime("%Y/%m/%d")

                if not name or not voyage:
                    return self.send_json({"success": False, "message": "Vessel Name & Voyage are required"}, 400)

                cursor.execute("INSERT INTO vessels VALUES (?,?,?,?,?,?,'BERTHED')", (v_id, name, voyage, berth, arrival, units))
                conn.commit()
                return self.send_json({"success": True, "message": f"Vessel '{name}' added to berth registry."})

            elif path.endswith("/api/admin/add-chassis"):
                vin = data.get("vin", "").strip().upper()
                vessel_id = data.get("vessel_id", "VSL001")
                model = data.get("model", "VEZEL").strip().upper()
                used = data.get("brand_new_used", "USED")
                color = data.get("color", "White")
                yard = data.get("yard", "Yard A")
                row_lane = data.get("row_lane", "Block 1-Row 1")

                if not vin or len(vin) < 6:
                    return self.send_json({"success": False, "message": "Valid VIN required (min 6 chars)"}, 400)

                last_6 = vin[-6:]
                iid = f"ROV#{datetime.now().strftime('%M%S')}-01099"

                cursor.execute("INSERT INTO chassis VALUES (?,?,?,?,?,?,?,?,?,?,'No Tally')",
                               (vin, last_6, vessel_id, model, used, iid, color, 'Deck 1', yard, row_lane))
                conn.commit()
                return self.send_json({"success": True, "message": f"Chassis VIN '{vin}' added to BTOS registry."})

            elif path.endswith("/api/tally/ai-scan"):
                detected_items = {
                    "MONO GRAM": True, "WIPERS": True, "TOW CAP": True, "SIDE MIRROR - RIGHT": True,
                    "SIDE MIRROR - LEFT": True, "HUB CAPS": False, "WHEEL CUP": True, "ANTENNA": True,
                    "SPARE TYRE": True, "WHEEL BRUSH": False, "JACK": True, "TOOL KIT": True,
                    "AIR PUMP": False, "GUM BOTTLE": False, "REVERSE CAMERA": True, "ALLOY": True,
                    "A_C_NOB": True, "GEAR NOB": True, "REMOTE_KEY": "01", "CARPETS": True, "TV SCREEN - FRONT": True
                }
                suggested_damages = [
                    {"type": "Scratched", "location": "Right Side Mirror Housing (AI Detected - 94% Confidence)", "code": 6},
                    {"type": "Pitted", "location": "Front Windshield (AI Detected - 88% Confidence)", "code": 10}
                ]
                return self.send_json({"success": True, "ai_items": detected_items, "ai_damages": suggested_damages, "confidence": "HIGH (96.4%)"})

            elif path.endswith("/api/security-check"):
                vin = data.get("vin")
                sec_status = data.get("status", "Verified")
                discrepancies = json.dumps(data.get("discrepancies", []))
                remarks = data.get("remarks", "")
                user_id = data.get("user_id", "Security 5958")

                cursor.execute("SELECT id FROM security_checks WHERE vin = ?", (vin,))
                existing = cursor.fetchone()

                if existing:
                    cursor.execute("""
                        UPDATE security_checks SET status = ?, discrepancies_json = ?, remarks = ?, checked_by = ?, checked_at = ? WHERE vin = ?
                    """, (sec_status, discrepancies, remarks, user_id, now_str, vin))
                else:
                    cursor.execute("""
                        INSERT INTO security_checks (vin, status, discrepancies_json, remarks, checked_by, checked_at) VALUES (?, ?, ?, ?, ?, ?)
                    """, (vin, sec_status, discrepancies, remarks, user_id, now_str))

                cursor.execute("UPDATE chassis SET tally_status = ? WHERE vin = ?", (sec_status, vin))
                cursor.execute("""
                    INSERT INTO audit_trail (vin, work_point, user_id, user_role, timestamp, details) VALUES (?, ?, ?, ?, ?, ?)
                """, (vin, "Security Check", user_id, "Security Officer", now_str, f"Security Check: {sec_status}. Remarks: {remarks}"))

                database.queue_sync_event(cursor, "SECURITY_VERIFIED", vin, {
                    "vin": vin,
                    "status": sec_status,
                    "discrepancies": data.get("discrepancies", []),
                    "remarks": remarks,
                    "user_id": user_id,
                    "timestamp": now_str
                })

                conn.commit()
                return self.send_json({"success": True, "message": f"Security check recorded as {sec_status}"})

            elif path.endswith("/api/update-approval/request"):
                vin = data.get("vin")
                user_id = data.get("user_id", "Surveyor 298")
                reason = data.get("reason", "Needs accessory count adjustment after yard inspection")

                cursor.execute("INSERT INTO update_approvals (vin, requested_by, reason, status, updated_at) VALUES (?, ?, ?, 'PENDING', ?)", (vin, user_id, reason, now_str))
                cursor.execute("INSERT INTO audit_trail (vin, work_point, user_id, user_role, timestamp, details) VALUES (?, ?, ?, ?, ?, ?)", (vin, "Update Request", user_id, "Surveyor", now_str, f"Tally Update Requested: {reason}"))
                conn.commit()
                return self.send_json({"success": True, "message": "Tally update request submitted for supervisor approval."})

            elif path.endswith("/api/update-approval/respond"):
                approval_id = data.get("approval_id")
                action = data.get("action", "APPROVE")
                user_id = data.get("user_id", "Supervisor 352")

                new_status = "APPROVED" if action == "APPROVE" else "REJECTED"
                cursor.execute("UPDATE update_approvals SET status = ?, approved_by = ?, updated_at = ? WHERE id = ?", (new_status, user_id, now_str, approval_id))

                cursor.execute("SELECT vin FROM update_approvals WHERE id = ?", (approval_id,))
                row = cursor.fetchone()
                if row:
                    vin = row["vin"]
                    cursor.execute("INSERT INTO audit_trail (vin, work_point, user_id, user_role, timestamp, details) VALUES (?, ?, ?, ?, ?, ?)", (vin, "Update Approval", user_id, "Supervisor", now_str, f"Tally Update Request {new_status} by {user_id}"))

                conn.commit()
                return self.send_json({"success": True, "message": f"Approval request {new_status}"})

            elif path.endswith("/api/bulk-inquire"):
                vins_input = data.get("vins", [])
                matched = []
                unmatched = []

                for raw_vin in vins_input:
                    v = raw_vin.strip().upper()
                    if not v:
                        continue
                    
                    cursor.execute("""
                        SELECT c.*, v.name as vessel_name, v.voyage, t.status as tally_doc_status, t.doc_ref
                        FROM chassis c 
                        LEFT JOIN vessels v ON c.vessel_id = v.id 
                        LEFT JOIN tally_sheets t ON c.vin = t.vin
                        WHERE c.vin = ? OR c.last_6 = ?
                    """, (v, v))
                    row = cursor.fetchone()
                    if row:
                        matched.append(dict(row))
                    else:
                        unmatched.append(v)

                return self.send_json({"success": True, "matched": matched, "unmatched": unmatched, "total_searched": len(matched) + len(unmatched)})

            else:
                return self.send_json({"success": False, "message": f"Unknown API POST endpoint: {path}"}, 404)

        finally:
            conn.close()

    def do_DELETE(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        conn = database.get_db()
        cursor = conn.cursor()

        try:
            if "/api/users/" in path:
                user_id = path.split("/api/users/")[-1].strip()
                cursor.execute("UPDATE users SET status = 'INACTIVE' WHERE id = ?", (user_id,))
                conn.commit()
                return self.send_json({"success": True, "message": f"User ID {user_id} deactivated."})
            else:
                return self.send_json({"success": False, "message": "Invalid DELETE endpoint"}, 400)
        finally:
            conn.close()
