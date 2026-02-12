import pandas as pd
import datetime
import tkinter as tk
from tkinter import filedialog, messagebox
import os

# --- Rules & Mapping ---
FIELD_GROUPS = {
    'U4': ['OG6AW', 'OG6AE', 'OG6BW', 'OG6BE', 'OG6CE', 'OG6CW'],
    'U5': ['OG6AW', 'OG6AE', 'OG6BW', 'OG6BE', 'OG6CE', 'OG6CW'],
    'U6': ['OG6AW', 'OG6AE', 'OG6BW', 'OG6BE', 'OG6CE', 'OG6CW'],
    'U7': ['OG6AW', 'OG6AE', 'OG6BW', 'OG6BE', 'OG6CE', 'OG6CW'],
    'U8': ['OG6AW', 'OG6AE', 'OG6BW', 'OG6BE', 'OG6CE', 'OG6CW'],
    'U9': ['OG4AW', 'OG4AE', 'OG4BW', 'OG4BE', 'OG5AW', 'OG5AE', 'OG5BW', 'OG5BE'],
    'U10': ['OG4AW', 'OG4AE', 'OG4BW', 'OG4BE', 'OG5AW', 'OG5AE', 'OG5BW', 'OG5BE'],
    'U11': ['MM3N', 'MM3S', 'MM5AW', 'MM5AE', 'MM5BW', 'MM5BE'],
    'U12': ['MM3N', 'MM3S', 'MM5AW', 'MM5AE', 'MM5BW', 'MM5BE'],
    'U13': ['MM1N', 'MM1S', 'MM2N', 'MM2S', 'MM4N', 'MM4S', 'MM6N', 'MM6S', 'OG1N', 'OG1S', 'OG2N', 'OG3N', 'OG3S'],
    'U14': ['MM1N', 'MM1S', 'MM2N', 'MM2S', 'MM4N', 'MM4S', 'MM6N', 'MM6S', 'OG1N', 'OG1S', 'OG2N', 'OG3N', 'OG3S'],
    'U16': ['MM1N', 'MM1S', 'MM2N', 'MM2S', 'MM4N', 'MM4S', 'MM6N', 'MM6S', 'OG1N', 'OG1S', 'OG2N', 'OG3N', 'OG3S'],
    'U17': ['MM1N', 'MM1S', 'MM2N', 'MM2S', 'MM4N', 'MM4S', 'MM6N', 'MM6S', 'OG1N', 'OG1S', 'OG2N', 'OG3N', 'OG3S'],
    'U18': ['MM1N', 'MM1S', 'MM2N', 'MM2S', 'MM4N', 'MM4S', 'MM6N', 'MM6S', 'OG1N', 'OG1S', 'OG2N', 'OG3N', 'OG3S'],
    'U19': ['MM1N', 'MM1S', 'MM2N', 'MM2S', 'MM4N', 'MM4S', 'MM6N', 'MM6S', 'OG1N', 'OG1S', 'OG2N', 'OG3N', 'OG3S'],
}

DAY_MAP = {'Monday': 'Mon', 'Tuesday': 'Tue', 'Wednesday': 'Wed', 'Thursday': 'Thu', 'Friday': 'Fri', 'Saturday': 'Sat', 'Sunday': 'Sun'}

def parse_time_slots(day, time_range):
    try:
        day_abbr = DAY_MAP.get(day)
        clean = str(time_range).lower().replace(' ', '')
        suffix = 'pm' if 'pm' in clean else 'am'
        times = clean.replace('pm', '').replace('am', '').split('-')

        def to_dt(t, sfx):
            if ':' not in t: t = f"{t}:00"
            return datetime.datetime.strptime(f"{t}{sfx}", "%I:%M%p")

        start_dt = to_dt(times[0], suffix)
        end_dt = to_dt(times[1], suffix)
        if start_dt > end_dt and suffix == 'pm':
            start_dt = to_dt(times[0], 'am')

        slots = []
        curr = start_dt
        while curr < end_dt:
            t_str = curr.strftime("%I:%M%p").lower().lstrip('0')
            slots.append(f"{day_abbr} {t_str}")
            curr += datetime.timedelta(minutes=30)
        return slots
    except:
        return []

def run_assignment(req_path, res_path):
    req_df = pd.read_excel(req_path)
    res_df = pd.read_excel(res_path)

    # Ensure field columns allow text
    for col in res_df.columns[1:]:
        res_df[col] = res_df[col].astype(object)

    time_col = res_df.columns[0]
    placed, unplaced = [], []

    for _, row in req_df.iterrows():
        coach = row['Coaches Name']
        age, loc = str(row['Team Age']).strip(), row['Location Preferred']
        day, time_pref = row['Day Preferred'], row['Time Preferred']

        # 1. Location Rule Check
        if loc not in ['Oak Grove', 'Meadowmere']:
            unplaced.append(f"COACH: {coach} | REASON: Location '{loc}' is outside automated scope (Oak Grove & Meadowmere only).")
            continue

        # 2. Time Format Check
        slots = parse_time_slots(day, time_pref)
        if not slots:
            unplaced.append(f"COACH: {coach} | REASON: Time format '{time_pref}' could not be read. Check if it matches '6-7pm'.")
            continue

        # 3. Age Group Eligibility Check
        eligible = [f for f in FIELD_GROUPS.get(age, []) if (loc == 'Oak Grove' and f.startswith('OG')) or (loc == 'Meadowmere' and f.startswith('MM'))]
        if not eligible:
            unplaced.append(f"COACH: {coach} | REASON: Age Group {age} is not permitted to practice at {loc} fields per GSSA rules.")
            continue

        # 4. Field Availability Check
        assigned = False
        tried_fields = []
        for field in eligible:
            if field not in res_df.columns:
                continue

            tried_fields.append(field)
            is_free = True
            conflicts = []

            for slot in slots:
                if slot not in res_df[time_col].values:
                    is_free = False
                    conflicts.append(f"Time slot {slot} not found in schedule")
                    break
                val = res_df.loc[res_df[time_col] == slot, field].values[0]
                if pd.notna(val) and str(val).strip() != "":
                    is_free = False
                    conflicts.append(f"{slot} taken by {val}")
                    break

            if is_free:
                for slot in slots:
                    res_df.loc[res_df[time_col] == slot, field] = str(coach)
                placed.append(f"COACH: {coach} -> ASSIGNED: {field} ({day} {time_pref})")
                assigned = True; break

        if not assigned:
            fields_str = ", ".join(tried_fields)
            unplaced.append(f"COACH: {coach} | REASON: Conflict. All eligible fields ({fields_str}) were occupied during {day} {time_pref}.")

    # Save Excel
    out_path = os.path.join(os.path.dirname(res_path), "ASSIGNED_Fields.xlsx")
    res_df.to_excel(out_path, index=False)

    # Save Report
    report_path = os.path.join(os.path.dirname(res_path), "assignment_report.txt")
    with open(report_path, "w") as f:
        f.write("=== GSSA FIELD ASSIGNMENT REPORT ===\n")
        f.write(f"Generated on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"TOTAL PLACED: {len(placed)}\n")
        f.write(f"TOTAL UNPLACED: {len(unplaced)}\n\n")
        f.write("--- SUCCESSFUL ASSIGNMENTS ---\n")
        f.write("\n".join(placed) if placed else "None")
        f.write("\n\n--- UNPLACED COACHES (ACTION REQUIRED) ---\n")
        f.write("\n".join(unplaced) if unplaced else "None")

    return out_path, report_path, len(placed), len(unplaced)

# --- GUI Setup ---
def start_app():
    root = tk.Tk()
    root.title("GSSA Field Assigner Pro")
    root.geometry("600x400")

    req_path, res_path = tk.StringVar(), tk.StringVar()

    tk.Label(root, text="Step 1: GSSA Practice Request File (.xlsx)", font=("Arial", 10, "bold")).pack(pady=5)
    tk.Button(root, text="Select Request File", command=lambda: req_path.set(filedialog.askopenfilename())).pack()
    tk.Label(root, textvariable=req_path, fg="gray", wraplength=500).pack()

    tk.Label(root, text="Step 2: Master Reservation File (.xlsx)", font=("Arial", 10, "bold")).pack(pady=5)
    tk.Button(root, text="Select Reservation File", command=lambda: res_path.set(filedialog.askopenfilename())).pack()
    tk.Label(root, textvariable=res_path, fg="gray", wraplength=500).pack()

    def process():
        if not req_path.get() or not res_path.get():
            messagebox.showwarning("Missing Files", "Please select both Excel files before running.")
            return
        try:
            excel_out, txt_out, p_count, u_count = run_assignment(req_path.get(), res_path.get())
            msg = f"Processing Complete!\n\nPlaced: {p_count}\nUnplaced: {u_count}\n\nNew Schedule: {os.path.basename(excel_out)}\nReport: {os.path.basename(txt_out)}"
            messagebox.showinfo("Success", msg)
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred:\n{e}")

    tk.Button(root, text="PROCESS ASSIGNMENTS", bg="#28a745", fg="white", font=("Arial", 12, "bold"), height=2, width=25, command=process).pack(pady=30)
    root.mainloop()

if __name__ == "__main__":
    start_app()