import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3, re, os, csv
from datetime import datetime

BASE=os.path.dirname(os.path.abspath(__file__))
DB=os.path.join(BASE,"data","phone_lookup.db")
REPORTS=os.path.join(BASE,"reports")
os.makedirs(os.path.dirname(DB),exist_ok=True)
os.makedirs(REPORTS,exist_ok=True)

COUNTRIES={
    "+91":("India","IN"), "+1":("United States/Canada","US/CA"),
    "+44":("United Kingdom","GB"), "+61":("Australia","AU"),
    "+81":("Japan","JP"), "+49":("Germany","DE"),
    "+33":("France","FR"), "+971":("United Arab Emirates","AE"),
    "+880":("Bangladesh","BD"), "+92":("Pakistan","PK")
}

def init_db():
    c=sqlite3.connect(DB)
    c.execute("""CREATE TABLE IF NOT EXISTS history(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        phone TEXT, country TEXT, country_code TEXT,
        number_type TEXT, status TEXT, searched_at TEXT)""")
    c.commit(); c.close()

def normalize(s):
    return re.sub(r"[\\s\\-()]", "", s.strip())

def lookup():
    raw=phone.get().strip()
    n=normalize(raw)
    if not n:
        messagebox.showwarning("Input","Please enter a phone number.")
        return
    if not re.fullmatch(r"\+?\d{7,15}",n):
        result.set("Invalid format. Use digits with optional + country code.")
        return

    country="Unknown"
    code="Unknown"
    for prefix,(name,cc) in sorted(COUNTRIES.items(),key=lambda x:-len(x[0])):
        if n.startswith(prefix):
            country=name; code=cc; break

    if n.startswith("+"):
        number_type="International"
    else:
        number_type="Local/Unspecified"

    status="Valid format"
    result.set(f"Country: {country}\\nRegion code: {code}\\nType: {number_type}\\nStatus: {status}")

    c=sqlite3.connect(DB)
    c.execute("""INSERT INTO history(phone,country,country_code,number_type,status,searched_at)
                 VALUES(?,?,?,?,?,?)""",
              (n,country,code,number_type,status,datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    c.commit(); c.close()
    load_history()

def load_history():
    tree.delete(*tree.get_children())
    c=sqlite3.connect(DB)
    for row in c.execute("SELECT id,phone,country,country_code,number_type,status,searched_at FROM history ORDER BY id DESC"):
        tree.insert("", "end", values=row)
    c.close()

def export_history():
    c=sqlite3.connect(DB)
    rows=c.execute("SELECT id,phone,country,country_code,number_type,status,searched_at FROM history").fetchall()
    c.close()
    path=os.path.join(REPORTS,"phone_lookup_history.csv")
    with open(path,"w",newline="",encoding="utf-8") as f:
        w=csv.writer(f)
        w.writerow(["ID","Phone","Country","Country Code","Type","Status","Searched At"])
        w.writerows(rows)
    messagebox.showinfo("Export Complete",f"Saved to:\\n{path}")

def clear_history():
    if messagebox.askyesno("Confirm","Delete all local search history?"):
        c=sqlite3.connect(DB); c.execute("DELETE FROM history"); c.commit(); c.close()
        load_history()

init_db()
root=tk.Tk()
root.title("Phone Information Lookup System")
root.geometry("900x650")
root.configure(bg="#111827")

tk.Label(root,text="PHONE INFORMATION LOOKUP",font=("Arial",24,"bold"),
         fg="white",bg="#111827").pack(pady=(20,5))
tk.Label(root,text="Safe lookup • No GPS tracking • No private identity data",
         font=("Arial",11),fg="#b9c2d0",bg="#111827").pack(pady=(0,18))

main=tk.Frame(root,bg="#111827"); main.pack(fill="x",padx=30)
tk.Label(main,text="Phone Number:",font=("Arial",13,"bold"),
         fg="white",bg="#111827").grid(row=0,column=0,padx=8,pady=8,sticky="w")
phone=tk.StringVar()
tk.Entry(main,textvariable=phone,font=("Arial",14),width=35).grid(row=0,column=1,padx=8,pady=8)
tk.Button(main,text="Lookup",command=lookup,font=("Arial",11,"bold"),
          bg="#2563eb",fg="white",width=12).grid(row=0,column=2,padx=8)

result=tk.StringVar(value="Enter a number to check its basic format and country code.")
tk.Label(root,textvariable=result,justify="left",anchor="w",font=("Arial",12),
         fg="white",bg="#1f2937",padx=15,pady=15).pack(fill="x",padx=30,pady=15)

frame=tk.Frame(root,bg="#111827"); frame.pack(fill="both",expand=True,padx=30,pady=5)
tk.Label(frame,text="Local Search History",font=("Arial",14,"bold"),
         fg="white",bg="#111827").pack(anchor="w")

cols=("id","phone","country","country_code","number_type","status","searched_at")
tree=ttk.Treeview(frame,columns=cols,show="headings")
for col in cols:
    tree.heading(col,text=col.replace("_"," ").title())
    tree.column(col,width=120)
tree.pack(fill="both",expand=True,pady=8)

bar=tk.Frame(root,bg="#111827"); bar.pack(pady=10)
tk.Button(bar,text="Export CSV",command=export_history,width=14).pack(side="left",padx=5)
tk.Button(bar,text="Clear History",command=clear_history,width=14).pack(side="left",padx=5)

load_history()
root.mainloop()
