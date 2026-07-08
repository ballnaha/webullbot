import os
import sys
import time
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.align import Align
from rich.columns import Columns
from rich.prompt import Prompt, IntPrompt, Confirm

from config import Config
from clients import get_client
from strategies import get_strategy
from bot import TradingBot

console = Console()

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def show_banner():
    banner_text = """
 [bold cyan]=======================================================[/bold cyan]
 [bold gold1]   __      __        _bull  _______                  _ [/bold gold1]
 [bold gold1]   \ \    / /       | |    |__   __|                | |[/bold gold1]
 [bold gold1]    \ \  / /_      _| |__     | |_ __ __ _  ___   __| |[/bold gold1]
 [bold gold1]     \ \/ /| _ \  / _` '_ \    | | '__/ _` |/ _ \ / _` |[/bold gold1]
 [bold gold1]      \  / |  __/| (_| |_) |   | | | | (_| |  __/| (_| |[/bold gold1]
 [bold gold1]       \/   \___| \__,_.__/    |_|_|  \__,_|\___| \__,_|[/bold gold1]
 [bold cyan]=======================================================[/bold cyan]
 [italic white]            Webull Trading Bot & Simulator - Python [/italic white]
    """
    console.print(banner_text)

def run_setup_wizard():
    """
    Interactive setup wizard to configure the .env file.
    """
    clear_screen()
    show_banner()
    console.print("[bold yellow]⚙️ Setup Wizard - บอทเทรด Webull[/bold yellow]\n")
    console.print("ระบบจะช่วยคุณตั้งค่าไฟล์คอนฟิกูเรชัน (.env) เพื่อเริ่มใช้งานบอทได้อย่างรวดเร็ว\n")

    # 1. Select Trading Mode
    console.print("[bold green]ขั้นตอนที่ 1: เลือกโหมดการเทรด[/bold green]")
    console.print("  [1] [bold cyan]LOCAL_PAPER[/bold cyan] - จำลองการเทรดออฟไลน์ (ปลอดภัยที่สุด ไม่ต้องใช้บัญชี)")
    console.print("  [2] [bold cyan]WEBULL_PAPER[/bold cyan] - บัญชีจำลองของ Webull (ต้องมีบัญชีเพื่อเข้าสู่ระบบ)")
    console.print("  [3] [bold cyan]WEBULL_LIVE[/bold cyan] - เทรดพอร์ตจริงผ่าน Webull (มีความเสี่ยงสูง ต้องมีบัญชี + PIN)")
    console.print("  [4] [bold cyan]WEBULL_OFFICIAL[/bold cyan] - เทรดพอร์ตจริงผ่าน Webull OpenAPI (สำหรับผู้ใช้ที่ได้รับสิทธิ์)")
    
    choice = Prompt.ask("เลือกโหมด (1-4)", choices=["1", "2", "3", "4"], default="1")
    
    mode_map = {
        "1": "LOCAL_PAPER",
        "2": "WEBULL_PAPER",
        "3": "WEBULL_LIVE",
        "4": "WEBULL_OFFICIAL"
    }
    trade_mode = mode_map[choice]

    username = ""
    password = ""
    trade_pin = ""
    app_key = ""
    app_secret = ""

    # 2. Collect Credentials based on mode
    if trade_mode in ["WEBULL_PAPER", "WEBULL_LIVE"]:
        console.print("\n[bold green]ขั้นตอนที่ 2: กรอกข้อมูลบัญชี Webull Unofficial[/bold green]")
        username = Prompt.ask("อีเมล หรือ เบอร์โทรศัพท์ (รูปแบบ: +66-xxxxxxxxx)")
        password = Prompt.ask("รหัสผ่าน Webull", password=True)
        if trade_mode == "WEBULL_LIVE":
            trade_pin = Prompt.ask("รหัส PIN 6 หลักสำหรับทำรายการ", password=True)
            
    elif trade_mode == "WEBULL_OFFICIAL":
        console.print("\n[bold green]ขั้นตอนที่ 2: กรอกข้อมูล Webull OpenAPI[/bold green]")
        app_key = Prompt.ask("Webull OpenAPI App Key")
        app_secret = Prompt.ask("Webull OpenAPI App Secret", password=True)

    # 3. Collect Strategy parameters
    console.print("\n[bold green]ขั้นตอนที่ 3: ตั้งค่ากลยุทธ์ซื้อขาย[/bold green]")
    symbols = Prompt.ask("หุ้นที่ต้องการติดตาม (คั่นด้วยจุลภาค เช่น AAPL,MSFT,TSLA)", default="AAPL,MSFT,TSLA")
    qty = IntPrompt.ask("จำนวนหุ้นต่อการสั่งซื้อ 1 ครั้ง", default=1)
    interval = IntPrompt.ask("ความถี่ในการตรวจสอบราคาและสั่งเทรด (วินาที เช่น 60)", default=60)
    period = Prompt.ask("ช่วงเวลาแท่งเทียน (m1, m5, m15, m30, h1, d)", choices=["m1", "m5", "m15", "m30", "h1", "d"], default="m5")

    # 4. Save to .env
    with open(".env", "w", encoding="utf-8") as f:
        f.write(f"TRADE_MODE={trade_mode}\n\n")
        f.write(f"WEBULL_USERNAME={username}\n")
        f.write(f"WEBULL_PASSWORD={password}\n")
        f.write(f"WEBULL_TRADE_PIN={trade_pin}\n")
        f.write("WEBULL_DEVICE_NAME=PythonBot\n\n")
        f.write(f"WEBULL_APP_KEY={app_key}\n")
        f.write(f"WEBULL_APP_SECRET={app_secret}\n\n")
        f.write(f"DEFAULT_SYMBOLS={symbols}\n")
        f.write(f"TRADE_QUANTITY={qty}\n")
        f.write(f"INTERVAL={interval}\n")
        f.write(f"CANDLE_PERIOD={period}\n")
        f.write("SIMULATED_INITIAL_CASH=10000.0\n")

    console.print("\n[bold green]🎉 บันทึกการตั้งค่าลงไฟล์ .env เรียบร้อยแล้ว![/bold green]")
    # Reload Config variables
    import importlib
    import config
    importlib.reload(config)
    time.sleep(1.5)

def draw_dashboard(bot: TradingBot, data: dict):
    """
    Clears screen and draws a beautiful CLI dashboard.
    """
    clear_screen()
    show_banner()

    # Get data
    balance = data.get("balance", {"cash": 0.0, "net_liquidation": 0.0, "unrealized_pnl": 0.0, "currency": "USD"})
    positions = data.get("positions", [])
    logs = data.get("logs", [])
    trades = data.get("trades", [])

    # Header Panel
    strategy_name = bot.strategy.name
    mode_style = "bold red" if Config.TRADE_MODE == "WEBULL_LIVE" else "bold green"
    header_text = Text()
    header_text.append("โหมดเทรด: ", style="bold white")
    header_text.append(Config.TRADE_MODE, style=mode_style)
    header_text.append(" | ", style="bold grey37")
    header_text.append("กลยุทธ์: ", style="bold white")
    header_text.append(strategy_name, style="bold yellow")
    header_text.append(" | ", style="bold grey37")
    header_text.append("อัปเดตล่าสุด: ", style="bold white")
    header_text.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), style="bold cyan")
    
    console.print(Panel(Align.center(header_text), border_style="cyan"))

    # Balance and Account Panel (Left Column equivalent)
    bal_table = Table(show_header=False, expand=True, box=None)
    bal_table.add_column("Key", style="bold white")
    bal_table.add_column("Value", justify="right")
    
    pnl_val = balance.get('unrealized_pnl', 0.0)
    pnl_style = "bold green" if pnl_val >= 0 else "bold red"
    pnl_sign = "+" if pnl_val > 0 else ""
    
    bal_table.add_row("💵 เงินสดคงเหลือ (Cash Balance)", f"${balance.get('cash', 0.0):,.2f}")
    bal_table.add_row("📈 มูลค่าพอร์ตรวม (Net Liquidation)", f"${balance.get('net_liquidation', 0.0):,.2f}")
    bal_table.add_row("📊 กำไร/ขาดทุนที่ยังไม่เกิดขึ้น (Unrealized P&L)", f"[{pnl_style}]{pnl_sign}${pnl_val:,.2f}[/{pnl_style}]")
    bal_table.add_row("💱 สกุลเงิน (Currency)", balance.get('currency', 'USD'))
    
    console.print(Panel(bal_table, title="[bold gold1]💳 ข้อมูลบัญชีซื้อขาย[/bold gold1]", border_style="gold1"))

    # Positions Table
    pos_table = Table(title="[bold green]📁 หุ้นในครอบครอง (Current Positions)[/bold green]", expand=True)
    pos_table.add_column("หุ้น (Symbol)", style="cyan bold")
    pos_table.add_column("จำนวน (Qty)", justify="right")
    pos_table.add_column("ราคาทุนเฉลี่ย (Avg Price)", justify="right")
    pos_table.add_column("มูลค่าตลาด (Market Value)", justify="right")
    pos_table.add_column("กำไร/ขาดทุน (P&L)", justify="right")

    if not positions:
        pos_table.add_row("ไม่มีหุ้นในพอร์ตขณะนี้", "", "", "", "")
    else:
        for pos in positions:
            pnl = pos.get('unrealized_pnl', 0.0)
            pnl_style = "green" if pnl >= 0 else "red"
            sign = "+" if pnl > 0 else ""
            pos_table.add_row(
                pos.get('symbol'),
                str(pos.get('qty')),
                f"${pos.get('avg_price'):,.2f}",
                f"${pos.get('market_value'):,.2f}",
                f"[{pnl_style}]{sign}${pnl:,.2f}[/{pnl_style}]"
            )
    console.print(pos_table)

    # Split bottom area into Trades History & Live System Logs
    trade_table = Table(title="[bold yellow]📜 ประวัติการซื้อขายของบอท (Trades Log)[/bold yellow]", expand=True)
    trade_table.add_column("เวลา (Time)", style="dim")
    trade_table.add_column("หุ้น (Symbol)", style="cyan")
    trade_table.add_column("คำสั่ง (Action)")
    trade_table.add_column("จำนวน (Qty)", justify="right")
    trade_table.add_column("ราคา (Price)", justify="right")
    trade_table.add_column("สถานะ (Status)", style="bold")

    if not trades:
        trade_table.add_row("ยังไม่มีการทำธุรกรรมในรอบการทำงานนี้", "", "", "", "", "")
    else:
        # Show last 5 trades
        for trade in trades[-5:]:
            action_style = "bold green" if trade['action'] == "BUY" else "bold red"
            trade_table.add_row(
                trade['time'],
                trade['symbol'],
                f"[{action_style}]{trade['action']}[/{action_style}]",
                str(trade['qty']),
                f"${trade['price']:,.2f}",
                trade['status']
            )
    
    # System logs (last 6 logs)
    log_text = Text()
    for log in logs[-6:]:
        log_text.append(log + "\n")
        
    console.print(Columns([
        Panel(trade_table, border_style="yellow", expand=True),
        Panel(log_text, title="[bold white]🛠️ ล็อกระบบ (System Logs)[/bold white]", border_style="grey37", expand=True)
    ]))
    
    console.print("\n[dim]กด [bold white]Ctrl+C[/bold white] เพื่อหยุดการทำงานของบอทและกลับไปยังเมนูหลัก[/dim]")

def run_trading_bot():
    clear_screen()
    show_banner()
    
    # 1. Validate credentials
    ok, msg = Config.validate()
    if not ok:
        console.print(f"[bold red]❌ ข้อผิดพลาดในการตั้งค่า:[/bold red] {msg}")
        if Confirm.ask("ต้องการเปิดตัวช่วยตั้งค่า Setup Wizard หรือไม่?"):
            run_setup_wizard()
            # Retry validation
            ok, msg = Config.validate()
            if not ok:
                console.print("[bold red]ยังพบข้อผิดพลาดในการตั้งค่า ปิดการทำงาน บ๊ายบาย...[/bold red]")
                time.sleep(2)
                return
        else:
            return

    # 2. Select strategy
    console.print("\n[bold green]เลือกกลยุทธ์สำหรับรันบอท:[/bold green]")
    console.print("  [1] [bold yellow]SMA Crossover (10/30)[/bold yellow] - สัญญาณซื้อเมื่อสั้นตัดยาวขึ้น, สัญญาณขายเมื่อตัดลง")
    console.print("  [2] [bold yellow]RSI Strategy (14, 30/70)[/bold yellow] - สัญญาณเมื่อหลุดเขต Oversold หรือ Overbought")
    
    strat_choice = Prompt.ask("เลือกกลยุทธ์ (1-2)", choices=["1", "2"], default="1")
    
    if strat_choice == "1":
        strategy = get_strategy("sma", fast_period=10, slow_period=30)
    else:
        strategy = get_strategy("rsi", period=14, oversold=30.0, overbought=70.0)

    # 3. Create client and bot orchestrator
    with console.status("[bold cyan]🔄 กำลังเริ่มต้น Client และเชื่อมต่อ API...[/bold cyan]") as status:
        try:
            client = get_client()
            login_ok = client.login()
            if not login_ok:
                console.print("[bold red]❌ ล็อกอินไม่สำเร็จ กรุณาตรวจสอบข้อมูลใน .env[/bold red]")
                time.sleep(3)
                return
                
            bot = TradingBot(client=client, strategy=strategy)
        except Exception as e:
            console.print(f"[bold red]❌ เกิดข้อผิดพลาดร้ายแรงระหว่างเริ่มต้นบอท:[/bold red] {e}")
            time.sleep(4)
            return

    # 4. Core running loop
    console.print("[bold green]เริ่มต้นรันบอทสำเร็จ! กำลังเข้าสู่หน้าจอ Dashboard...[/bold green]")
    time.sleep(1)
    
    try:
        while True:
            # Run one iteration of the bot
            # This fetches info and checks signals
            bot_data = bot.run_once()
            
            # Redraw console screen
            draw_dashboard(bot, bot_data)
            
            # Sleep for interval
            time.sleep(Config.INTERVAL)
            
    except KeyboardInterrupt:
        console.print("\n[bold yellow]⚠️ ได้รับสัญญาณหยุดทำงานจากผู้ใช้! กำลังกลับสู่เมนูหลัก...[/bold yellow]")
        time.sleep(2)

def view_portfolio():
    clear_screen()
    show_banner()
    console.print("[bold cyan]🔍 รายงานพอร์ตการลงทุนปัจจุบัน[/bold cyan]\n")
    
    with console.status("[bold green]กำลังเชื่อมต่อเพื่ออ่านข้อมูล...[/bold green]"):
        try:
            client = get_client()
            if not client.login():
                console.print("[bold red]ไม่สามารถเข้าสู่ระบบเพื่อเช็คข้อมูลได้[/bold red]")
                time.sleep(2)
                return
            balance = client.get_account_balance()
            positions = client.get_positions()
        except Exception as e:
            console.print(f"[bold red]เกิดข้อผิดพลาด: {e}[/bold red]")
            time.sleep(2)
            return

    table = Table(title="ยอดเงินคงเหลือ")
    table.add_column("หัวข้อ", style="bold yellow")
    table.add_column("ยอดเงิน", justify="right")
    table.add_row("💵 เงินสดคงเหลือ (Cash Balance)", f"${balance['cash']:,.2f}")
    table.add_row("📈 มูลค่าพอร์ตรวม (Net Liquidation)", f"${balance['net_liquidation']:,.2f}")
    table.add_row("📊 กำไร/ขาดทุนที่ยังไม่รับรู้ (Unrealized P&L)", f"${balance['unrealized_pnl']:,.2f}")
    console.print(table)
    
    pos_table = Table(title="หุ้นที่มีอยู่")
    pos_table.add_column("หุ้น")
    pos_table.add_column("จำนวน", justify="right")
    pos_table.add_column("ราคาทุนเฉลี่ย", justify="right")
    pos_table.add_column("มูลค่ารวม", justify="right")
    pos_table.add_column("กำไร/ขาดทุนสะสม", justify="right")
    
    for pos in positions:
        pos_table.add_row(
            pos['symbol'],
            str(pos['qty']),
            f"${pos['avg_price']:,.2f}",
            f"${pos['market_value']:,.2f}",
            f"${pos['unrealized_pnl']:,.2f}"
        )
    console.print(pos_table)
    
    Prompt.ask("\nกด Enter เพื่อกลับไปเมนูหลัก")

def main():
    while True:
        clear_screen()
        show_banner()
        
        console.print("[bold yellow]เมนูหลัก (Main Menu)[/bold yellow]")
        console.print("  [1] [bold green]🚀 เริ่มทำงานระบบบอทเทรดหุ้นอัตโนมัติ (Start Trading Bot)[/bold green]")
        console.print("  [2] [bold cyan]🔎 ตรวจสอบพอร์ตการลงทุนปัจจุบัน (View Portfolio)[/bold cyan]")
        console.print("  [3] [bold blue]⚙️ ตั้งค่าไฟล์สิ่งแวดล้อมใหม่ (Setup Wizard / Configuration)[/bold blue]")
        console.print("  [4] [bold red]🚪 ออกจากโปรแกรม (Exit)[/bold red]")
        
        choice = Prompt.ask("\nเลือกคำสั่ง (1-4)", choices=["1", "2", "3", "4"], default="1")
        
        if choice == "1":
            run_trading_bot()
        elif choice == "2":
            view_portfolio()
        elif choice == "3":
            run_setup_wizard()
        elif choice == "4":
            console.print("[bold gold1]👋 ขอบคุณสำหรับการใช้งานบอทเทรด Webull ขอให้ท่านโชคดีในการลงทุน! Bye Bye.[/bold gold1]")
            sys.exit(0)

if __name__ == "__main__":
    # Ensure working directory matches workspace directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    main()
