# pip install toml rich
import toml
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, BarColumn, TextColumn

c = Console()

ASCII = r"""
  _____              .___             .__    .___ _________         __         .__                     
  /  _  \   ____    __| _/______  ____ |__| __| _/ \_   ___ \_____ _/  |______  |  |   ____   ____     
 /  /_\  \ /    \  / __ |\_  __ \/  _ \|  |/ __ |  /    \  \/\__  \\   __\__  \ |  |  /  _ \ / ___\   
/    |    \   |  \/ /_/ | |  | \(  <_> )  / /_/ |  \     \____/ __ \|  |  / __ \|  |_(  <_> ) /_/  > 
\____|__  /___|  /\____ | |__|   \____/|__\____ |   \______  (____  /__| (____  /____/\____/\___  /  
        \/     \/      \/                      \/          \/     \/          \/           /_____/   
"""

def scan(a,b):
    d={"versions":[], "libraries":[], "plugins":[]}
    for s in d:
        keys=set(a.get(s,{}))|set(b.get(s,{}))
        for k in keys:
            v1 = a.get(s,{}).get(k)
            v2 = b.get(s,{}).get(k)
            if v1 and v2 and v1 != v2: d[s].append(k)
    return d

def merge(a,b,s,mode,p=None):
    m=a.copy()
    for k,v in b.items():
        if k in m and m[k]!=v:
            if mode=="p": m[k]=m[k] if p=="f" else v
            elif mode=="m":
                c.print(f"[yellow]Conflict in [{s}] '{k}'[/yellow]")
                c.print(f"  [cyan]File1:[/cyan] {m[k]}")
                c.print(f"  [cyan]File2:[/cyan] {v}")
                ch=c.input("Keep (1) first, (2) second, (m) manual? [1/2/m]: ").strip().lower()
                m[k]= v if ch=="2" else c.input(f"Enter value for '{k}': ").strip() if ch=="m" else m[k]
        else: m[k]=v
    return m

def write_toml(d,out):
    with open(out,"w") as f:
        for s in ["versions","libraries","plugins"]:
            if s in d:
                f.write(f"[{s}]\n")
                for k,v in d[s].items():
                    if isinstance(v,dict):
                        p=[]
                        for key,val in v.items():
                            if key=="version" and isinstance(val,dict) and "ref" in val:
                                p.append(f'version.ref = "{val["ref"]}"')
                            else: p.append(f'{key} = "{val}"')
                        f.write(f"{k} = {{ {', '.join(p)} }}\n")
                    else: f.write(f'{k} = "{v}"\n')
                f.write("\n")

def merge_files(f1,f2,out,mode,p=None):
    a,b=toml.load(f1), toml.load(f2)
    conf=scan(a,b)
    tot=sum(len(v) for v in conf.values())

    if tot==0:
        c.print(Panel("[green]No conflicts detected[/green]",title="Scan"))
    else:
        t=Table(title="Conflict Summary")
        t.add_column("Section"); t.add_column("Count")
        for s,v in conf.items(): t.add_row(s,str(len(v)))
        c.print(t)

    merged={}
    if mode=="m":
        for s in ["versions","libraries","plugins"]:
            merged[s]=merge(a.get(s,{}),b.get(s,{}),s,mode,p)
    else:
        with Progress("[progress.description]{task.description}",BarColumn(),TextColumn("{task.completed}/{task.total}")) as pr:
            task=pr.add_task("Merging...", total=3)
            for s in ["versions","libraries","plugins"]:
                merged[s]=merge(a.get(s,{}),b.get(s,{}),s,mode,p)
                pr.update(task,advance=1)

    write_toml(merged,out)
    c.print(Panel(f"[green]Merged saved to {out}[/green]", title="Success"))

if __name__=="__main__":
    c.print(Panel(ASCII,title="libs.versions.toml Merger",style="bold cyan"))

    f1=c.input("Path to first TOML: ").strip()
    f2=c.input("Path to second TOML: ").strip()
    out=c.input("Output file (default merged_libs.versions.toml): ").strip() or "merged_libs.versions.toml"

    mode=c.input("Merge mode: [1] Priority [2] Manual: ").strip()
    if mode=="1":
        p=c.input("Priority file [1] First [2] Second: ").strip()
        p="f" if p=="1" else "s"
        merge_files(f1,f2,out,"p",p)
    else:
        merge_files(f1,f2,out,"m")
