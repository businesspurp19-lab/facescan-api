import tkinter as tk
from tkinter import messagebox, ttk
from ai.database_manager import LocalDatabaseManager
from ai.api_client import FaceScanAPIClient
from ai.attendance_logger import AttendanceLoggerCore
from ai.recognize import recognize_live_stream

class FaceScanDesktopApp:
    def __init__(self, root):
        self.root = root
        self.root.title("FaceScan - Instructor Terminal")
        self.root.geometry("480x550")
        self.root.resizable(False, False)
        
        # Core engines instantiation
        self.db = LocalDatabaseManager()
        self.api = FaceScanAPIClient()
        self.logger = AttendanceLoggerCore()
        
        # State management flags
        self.logged_in_instructor = None
        self.selected_load_data = None

        # Build structural view zones
        self.init_styles()
        self.show_login_frame()

    def init_styles(self):
        """Set up standard clean structural layout styles."""
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure('TLabel', font=('Helvetica', 10))
        self.style.configure('TButton', font=('Helvetica', 10, 'bold'), padding=6)
        self.style.configure('Header.TLabel', font=('Helvetica', 14, 'bold'))

    def clear_window(self):
        """Clears all structural widgets from the master root layout frame."""
        for widget in self.root.winfo_children():
            widget.destroy()

    def show_login_frame(self):
        self.clear_window()
        
        frame = ttk.Frame(self.root, padding="30")
        frame.pack(fill=tk.BOTH, expand=True)

        # Header Title
        title = ttk.Label(frame, text="FaceScan System Login", style='Header.TLabel')
        title.pack(pady=(10, 30))

        # Check real-time connection status boundary layer
        status_text = "Network State: ONLINE" if self.api.check_online_status() else "Network State: OFFLINE BUFFER"
        status_lbl = ttk.Label(frame, text=status_text, font=('Helvetica', 9, 'italic'))
        status_lbl.pack(pady=(0, 20))

        # Inputs
        ttk.Label(frame, text="Employee ID:").pack(anchor=tk.W, pady=(5, 2))
        self.ent_emp_id = ttk.Entry(frame, font=('Helvetica', 11), width=35)
        self.ent_emp_id.pack(pady=(0, 15))
        self.ent_emp_id.insert(0, "EMP-") # helper structural prefix

        ttk.Label(frame, text="Password:").pack(anchor=tk.W, pady=(5, 2))
        self.ent_pwd = ttk.Entry(frame, font=('Helvetica', 11), show="*", width=35)
        self.ent_pwd.pack(pady=(0, 25))

        # Login Button
        btn_login = ttk.Button(frame, text="Authenticate Terminal", command=self.handle_login, width=30)
        btn_login.pack(pady=10)

    def handle_login(self):
        emp_id = self.ent_emp_id.get().strip()
        pwd = self.ent_pwd.get().strip()

        if not emp_id or not pwd:
            messagebox.showwarning("Input Error", "Please provide complete credential layers data details.")
            return

        # 1. Subukan ang live authentication sa remote centralized server
        success, result = self.api.authenticate_instructor(emp_id, pwd)

        if success:
            instructor_data = result.get("instructor_data", {})
            self.logged_in_instructor = instructor_data
            
            # I-sync at i-download ang active load configurations data matrix
            loads, err = self.api.download_active_loads(instructor_data['instructor_id'])
            if loads is not None:
                # I-update ang local SQLite cache architecture framework
                self.db.sync_downloaded_loads(instructor_data['instructor_id'], loads)
            
            messagebox.showinfo("Success", f"Welcome back, {instructor_data.get('firstname')}!")
            self.show_dashboard_frame()
        else:
            # 2. Fallback: Kapag offline o nabigo ang central server connection check, subukan ang local buffer data mapping
            messagebox.showwarning("Offline Mode", "Central server unreachable or bad credentials. Checking local offline storage cache context.")
            
            # Sinusubukan nating kunin ang structure mula sa local matrix base sa Employee ID prefix field match
            local_user = self.db.get_cached_instructor_by_employee_id(emp_id) if hasattr(self.db, 'get_cached_instructor_by_employee_id') else None
            
            if local_user:
                self.logged_in_instructor = local_user
                messagebox.showinfo("Offline Success", f"Logged in via structural offline cache: Welcome back!")
                self.show_dashboard_frame()
            else:
                messagebox.showerror("Auth Error", f"Live verification failed and no offline profile match exists for this terminal.")

    def show_dashboard_frame(self):
        self.clear_window()
        
        frame = ttk.Frame(self.root, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)

        # Header Info
        firstname = self.logged_in_instructor.get('firstname', 'Faculty')
        lastname = self.logged_in_instructor.get('lastname', 'Member')
        inst_name = f"{firstname} {lastname}"
        ttk.Label(frame, text=f"Instructor: {inst_name}", style='Header.TLabel').pack(pady=(5, 15))

        # Dropdown configuration list setup para sa subject allocation tracking matrix
        ttk.Label(frame, text="Select Active Class Session Load:").pack(anchor=tk.W, pady=(5, 5))
        
        # Kuhanin ang active loads na nanggaling sa downloaded o locally cached structures
        self.loaded_matrix = self.db.get_cached_loads_by_instructor(self.logged_in_instructor['instructor_id'])
        
        dropdown_options = []
        for l in self.loaded_matrix:
            dropdown_options.append(f"{l['subject_code']} - {l['subject_name']} ({l['room']} | {l['schedule']})")

        self.cb_loads = ttk.Combobox(frame, values=dropdown_options, state="readonly", width=45, font=('Helvetica', 10))
        self.cb_loads.pack(pady=(0, 20))
        if dropdown_options:
            self.cb_loads.current(0)

        # Operational Control Buttons Row
        btn_start_scan = ttk.Button(frame, text="LAUNCH FACESCAN CAMERA ENGINE", command=self.start_camera_tracking, width=35)
        btn_start_scan.pack(pady=15)

        btn_sync = ttk.Button(frame, text="Trigger Transaction Queue Sync", command=self.sync_local_queue, width=35)
        btn_sync.pack(pady=5)

        btn_logout = ttk.Button(frame, text="Disconnect Session", command=self.show_login_frame, width=35)
        btn_logout.pack(pady=(30, 0))

    def sync_local_queue(self):
        """Manually command the synchronization system core matrix."""
        status = self.logger.trigger_background_sync()
        if status:
            messagebox.showinfo("Sync Success", "Local synchronization cycle execution loop completed successfully.")
        else:
            messagebox.showwarning("Sync Caution", "System network target unreachable. Transaction queue preserved offline.")

    def start_camera_tracking(self):
        selected_index = self.cb_loads.current()
        if selected_index == -1:
            messagebox.showwarning("Session Error", "Please select a valid subject structure load configuration.")
            return
            
        selected_load = self.loaded_matrix[selected_index]
        
        # Itakda ang control logger tracking scope indicators
        self.logger.set_active_session(
            instructor_id=selected_load['instructor_id'],
            subject_id=selected_load['subject_id'],
            load_id=selected_load['load_id']
        )
        
        # Itago pansamantala ang main interface dashboard upang maiwasan ang maling multiple window processing clicks
        self.root.withdraw()
        
        try:
            # I-trigger ang fully functional InsightFace/OpenCV live engine block process loop
            recognize_live_stream(self.logger)
        except Exception as e:
            messagebox.showerror("Runtime Exception", f"Camera subsystem encountered an operational layer fault: {str(e)}")
        finally:
            # Siguraduhing lumabas man o mag-crash ang openCV stream, muling lilitaw ang Tkinter layout
            self.root.deiconify()
            messagebox.showinfo("Session Terminated", "Camera interface monitoring loop closed. Returned to console terminal dashboard.")

if __name__ == "__main__":
    root = tk.Tk()
    app = FaceScanDesktopApp(root)
    root.mainloop()