"use client";

import { useState, useEffect, useCallback } from "react";
import { 
  ThemeProvider, 
  createTheme, 
  CssBaseline, 
  Container, 
  Card, 
  CardContent, 
  Typography, 
  Button, 
  Box, 
  Table, 
  TableBody, 
  TableCell, 
  TableContainer, 
  TableHead, 
  TableRow, 
  Paper, 
  TextField, 
  Select, 
  MenuItem, 
  FormControl, 
  InputLabel, 
  Switch, 
  FormControlLabel,
  Alert, 
  AlertTitle, 
  Divider, 
  Chip,
  Tabs,
  Tab,
  TablePagination,
  CircularProgress,
  Drawer,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton
} from '@mui/material';

import Header from 'frontend/components/Header';
import ConfirmDialog from 'frontend/components/ConfirmDialog';
import TradeDialog from 'frontend/components/TradeDialog';
import { useToast } from 'frontend/components/ToastProvider';

import { 
  Play, 
  Square, 
  Settings, 
  Wallet, 
  TrendingUp, 
  TrendingDown, 
  Activity, 
  Terminal, 
  History, 
  ArrowUpRight, 
  ArrowDownLeft, 
  RefreshCw, 
  AlertCircle,
  Database,
  Cpu,
  UserCheck,
  Eye,
  Trash2,
  Plus,
  ListPlus,
  X
} from 'lucide-react';

const API_BASE = "http://127.0.0.1:8484/api";

interface Balance {
  cash: number;
  net_liquidation: number;
  unrealized_pnl: number;
  currency: string;
}

interface Position {
  symbol: string;
  qty: number;
  avg_price: number;
  market_value: number;
  unrealized_pnl: number;
}

interface BotStatus {
  running: boolean;
  trade_mode: string;
  strategy: string;
  symbols: string[];
  quantity: number;
  quantity_hk: number;
  interval: number;
  candle_period: string;
  has_client: boolean;
}

interface SignalData {
  symbol: string;
  price: number;
  rsi: number;
  sma_fast: number;
  sma_slow: number;
  sma_signal: string;
  rsi_signal: string;
  hybrid_signal: string;
}

interface Trade {
  time: string;
  symbol: string;
  action: string;
  qty: number;
  price: number;
  status: string;
}

// Company Names Database for Tickers
const STOCK_NAMES: Record<string, string> = {
  // US Tickers
  "AAPL": "Apple Inc.",
  "MSFT": "Microsoft Corporation",
  "GOOGL": "Alphabet Inc.",
  "AMZN": "Amazon.com, Inc.",
  "TSLA": "Tesla, Inc.",
  "NVDA": "NVIDIA Corporation",
  
  // HK Tickers (with and without leading zeros for robustness)
  "700.HK": "Tencent Holdings Ltd.",
  "0700.HK": "Tencent Holdings Ltd.",
  "9988.HK": "Alibaba Group Holding Ltd.",
  "3690.HK": "Meituan",
  "9618.HK": "JD.com, Inc.",
  "9999.HK": "NetEase, Inc.",
  "1810.HK": "Xiaomi Corporation",
  "9888.HK": "Baidu, Inc.",
  "2318.HK": "Ping An Insurance Group",
  
  "3988.HK": "Bank of China Limited",
  "1398.HK": "Industrial and Commercial Bank of China",
  
  "939.HK": "China Construction Bank",
  "0939.HK": "China Construction Bank",
  
  "5.HK": "HSBC Holdings plc",
  "0005.HK": "HSBC Holdings plc",
  
  "1299.HK": "AIA Group Limited",
  
  "386.HK": "Sinopec Corp.",
  "0386.HK": "Sinopec Corp.",
  
  "857.HK": "PetroChina Company Limited",
  "0857.HK": "PetroChina Company Limited",
  
  "2628.HK": "China Life Insurance Company",
  
  "941.HK": "China Mobile Limited",
  "0941.HK": "China Mobile Limited",
  
  "2382.HK": "Sunny Optical Technology",
  "2015.HK": "Li Auto Inc.",
  "1211.HK": "BYD Company Limited",
  
  "981.HK": "SMIC",
  "0981.HK": "Semiconductor Manufacturing International Corp",
  
  "1024.HK": "Kuaishou Technology",
  
  "388.HK": "HKEX",
  "0388.HK": "Hong Kong Exchanges and Clearing Limited",
  
  "9868.HK": "XPeng Inc.",
  "2269.HK": "WuXi Biologics",
  "1818.HK": "Zhaojin Mining Industry Co., Ltd."
};

// Professional dark trading theme (metabot style)
const darkTheme = createTheme({
  palette: {
    mode: "dark",
    background: { default: "#07090e", paper: "#0f141c" },
    primary: { main: "#3b82f6" },
    secondary: { main: "#6366f1" },
    success: { main: "#16c784" },
    error: { main: "#ea3943" },
    warning: { main: "#f0a020" },
    text: { primary: "#f1f5f9", secondary: "#94a3b8" },
    divider: "rgba(148, 163, 184, 0.08)",
  },
  shape: { borderRadius: 16 },
  typography: {
    fontFamily: "Sarabun, var(--font-sans), ui-sans-serif, system-ui, -apple-system, sans-serif",
    h6: { fontWeight: 800, letterSpacing: 0 },
    button: { textTransform: "none", fontWeight: 600, borderRadius: 10 },
    overline: { letterSpacing: 0, fontWeight: 700 },
  },
  components: {
    MuiCard: {
      defaultProps: { elevation: 0 },
      styleOverrides: {
        root: {
          backgroundImage: "linear-gradient(180deg, #111827, #0f172a)",
          border: "1px solid rgba(148, 163, 184, 0.08)",
          boxShadow: "0 4px 20px -2px rgba(0, 0, 0, 0.4)",
          transition: "all 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
          "&:hover": {
            borderColor: "rgba(59, 130, 246, 0.15)",
            boxShadow: "0 8px 30px -4px rgba(0, 0, 0, 0.5), 0 0 15px rgba(59, 130, 246, 0.03)",
          },
        },
      },
    },
    MuiCssBaseline: {
      styleOverrides: {
        html: { overflowX: "hidden" },
        body: { overflowX: "hidden" },
      },
    },
    MuiPaper: { styleOverrides: { root: { backgroundImage: "none" } } },
    MuiButton: {
      defaultProps: { disableElevation: true },
      styleOverrides: {
        root: {
          borderRadius: 10,
          transition: "all 0.2s ease-in-out",
          "&:hover": {
            transform: "translateY(-1px)",
          },
          "&:active": {
            transform: "translateY(0)",
          },
        },
      },
    },
    MuiOutlinedInput: {
      styleOverrides: {
        root: {
          borderRadius: 10,
          backgroundColor: "rgba(255, 255, 255, 0.02)",
          transition: "all 0.2s ease-in-out",
          "& fieldset": {
            borderColor: "rgba(148, 163, 184, 0.12)",
          },
          "&:hover fieldset": {
            borderColor: "rgba(59, 130, 246, 0.3)",
          },
          "&.Mui-focused fieldset": {
            borderColor: "#3b82f6",
          },
        },
      },
    },
    MuiTableCell: {
      styleOverrides: {
        head: {
          fontWeight: 700,
          fontSize: '0.8rem',
          color: '#94a3b8',
          textTransform: 'uppercase',
          borderBottom: '1px solid rgba(148, 163, 184, 0.08)',
        },
        body: {
          fontSize: '0.9rem',
          borderBottom: '1px solid rgba(148, 163, 184, 0.04)',
        },
      },
    },
  },
});

export default function HongkongHome() {
  const { showToast } = useToast();
  const [mounted, setMounted] = useState(false);
  const [connected, setConnected] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);

  // Custom dialog states
  const [confirmClearOpen, setConfirmClearOpen] = useState(false);
  const [clearPending, setClearPending] = useState(false);
  const [tradeDialogOpen, setTradeDialogOpen] = useState(false);
  const [tradeDialogSymbol, setTradeDialogSymbol] = useState("");
  const [tradeDialogAction, setTradeDialogAction] = useState<"BUY" | "SELL">("BUY");
  const [tradeDialogDefaultQty, setTradeDialogDefaultQty] = useState(1);
  const [tradeDialogPending, setTradeDialogPending] = useState(false);

  // Data states
  const [status, setStatus] = useState<BotStatus>({
    running: false,
    trade_mode: "",
    strategy: "",
    symbols: [],
    quantity: 1,
    quantity_hk: 100,
    interval: 60,
    candle_period: "",
    has_client: false
  });

  const [balance, setBalance] = useState<Balance>({
    cash: 0.0,
    net_liquidation: 0.0,
    unrealized_pnl: 0.0,
    currency: "USD"
  });

  const [positions, setPositions] = useState<Position[]>([]);
  const [logs, setLogs] = useState<string[]>([]);
  const [trades, setTrades] = useState<Trade[]>([]);
  const [signals, setSignals] = useState<SignalData[]>([]);
  const [isSignalsLoading, setIsSignalsLoading] = useState(true);

  // UI States
  const [actionLoading, setActionLoading] = useState(false);
  const marketTab = 1 as number; // Fixed to Hong Kong Market for this page
  const [scanInterval, setScanInterval] = useState<number>(3); // Default 3s refresh
  const [isScanning, setIsScanning] = useState<boolean>(false);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10); // Default to 10 rows for optimal visual balance
  const [maxPrice, setMaxPrice] = useState<string>("20"); // Default to 20 as requested
  const [priceOperator, setPriceOperator] = useState<"le" | "ge">("le"); // Default to le (<=)
  
  // Watchlist Drawer States
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [drawerHkSymbols, setDrawerHkSymbols] = useState<string[]>([]);
  const [newSymbolInput, setNewSymbolInput] = useState("");

  const handleOpenDrawer = () => {
    setDrawerHkSymbols(status.symbols.filter(s => s.endsWith('.HK')));
    setDrawerOpen(true);
  };

  const handleAddSymbol = (symbol: string) => {
    let cleaned = symbol.trim().toUpperCase();
    if (!cleaned) return;
    if (!cleaned.endsWith('.HK')) cleaned += '.HK';
    
    // Basic HK stock ticker validation
    const numPart = cleaned.replace('.HK', '');
    if (!/^\d+$/.test(numPart)) {
      showToast("รหัสหุ้นฮ่องกงต้องเป็นตัวเลขเท่านั้น (เช่น 0700 หรือ 0700.HK)", "error");
      return;
    }
    
    // Pad with leading zeros to make it 4 digits
    let padded = numPart;
    if (padded.length < 4) {
      padded = padded.padStart(4, '0');
    }
    cleaned = padded + '.HK';
    
    if (!drawerHkSymbols.includes(cleaned)) {
      setDrawerHkSymbols([...drawerHkSymbols, cleaned]);
      setNewSymbolInput("");
    } else {
      showToast("มีหุ้นตัวนี้อยู่ในรายการแล้ว", "warning");
    }
  };

  const handleRemoveSymbol = (symbol: string) => {
    setDrawerHkSymbols(drawerHkSymbols.filter(s => s !== symbol));
  };

  const handleClearAllSymbols = async () => {
    setClearPending(true);
    const usList = status.symbols.filter(s => !s.endsWith('.HK'));
    
    try {
      const res = await fetch(`${API_BASE}/config`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          trade_mode: status.trade_mode,
          symbols: usList, // Clear HK list on backend by saving only US symbols
          quantity: status.quantity,
          quantity_hk: status.quantity_hk,
          interval: status.interval,
          candle_period: status.candle_period,
          strategy: status.strategy,
          username: "",
          password: "",
          trade_pin: "",
          app_key: "",
          app_secret: ""
        })
      });
      
      const data = await res.json();
      if (!res.ok) {
        showToast(`ล้มเหลวในการล้างข้อมูล: ${data.detail || "ข้อผิดพลาดระบบหลังบ้าน"}`, "error");
      } else {
        showToast("ล้างรายการหุ้นสแกนทั้งหมดและรีโหลดบอทสำเร็จ!", "success");
        setDrawerHkSymbols([]);
        setIsConfigInitialized(false);
        await loadData(true);
        setConfirmClearOpen(false);
      }
    } catch (err) {
      showToast("เกิดข้อผิดพลาดในการเชื่อมต่อเครือข่าย", "error");
    } finally {
      setClearPending(false);
    }
  };

  const handleSaveDrawerConfig = async () => {
    setActionLoading(true);
    const usList = status.symbols.filter(s => !s.endsWith('.HK'));
    const combinedSymbols = [...usList, ...drawerHkSymbols];
    
    try {
      const res = await fetch(`${API_BASE}/config`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          trade_mode: status.trade_mode,
          symbols: combinedSymbols,
          quantity: status.quantity,
          quantity_hk: status.quantity_hk,
          interval: status.interval,
          candle_period: status.candle_period,
          strategy: status.strategy,
          username: "",
          password: "",
          trade_pin: "",
          app_key: "",
          app_secret: ""
        })
      });
      
      const data = await res.json();
      if (!res.ok) {
        showToast(`เกิดข้อผิดพลาด: ${data.detail || "ไม่สามารถอัปเดตข้อมูลได้"}`, "error");
      } else {
        showToast("บันทึกการตั้งค่ารายชื่อหุ้นฮ่องกงและรีโหลดบอทสำเร็จ!", "success");
        setIsConfigInitialized(false);
        setDrawerOpen(false);
        await loadData(true);
      }
    } catch (err) {
      showToast("ไม่สามารถบันทึกได้ กรุณาลองใหม่อีกครั้ง", "error");
    } finally {
      setActionLoading(false);
    }
  };
  
  // Watchlist configuration reload indicator
  
  // Flag to lock config form resets during status updates
  const [isConfigInitialized, setIsConfigInitialized] = useState(false);

  // Config form state
  const [formMode, setFormMode] = useState("LOCAL_PAPER");
  const [formUsSymbols, setFormUsSymbols] = useState("");
  const [formHkSymbols, setFormHkSymbols] = useState("");
  const [formQty, setFormQty] = useState(1);
  const [formInterval, setFormInterval] = useState(60);
  const [formPeriod, setFormPeriod] = useState("m5");
  const [formStrategy, setFormStrategy] = useState("sma");
  
  // Credentials config inputs
  const [formUsername, setFormUsername] = useState("");
  const [formPassword, setFormPassword] = useState("");
  const [formTradePin, setFormTradePin] = useState("");
  const [formAppKey, setFormAppKey] = useState("");
  const [formAppSecret, setFormAppSecret] = useState("");

  const loadData = useCallback(async (forceLoading = false) => {
    if (forceLoading) {
      setIsSignalsLoading(true);
    }
    try {
      const resStatus = await fetch(`${API_BASE}/status`);
      if (!resStatus.ok) throw new Error("Backend response error");
      const dataStatus = await resStatus.json();
      setStatus(dataStatus);
      setConnected(true);
      setApiError(null);

      const resPort = await fetch(`${API_BASE}/portfolio`);
      if (resPort.ok) {
        const dataPort = await resPort.json();
        setBalance(dataPort.balance);
        setPositions(dataPort.positions);
      }

      const resHistory = await fetch(`${API_BASE}/history`);
      if (resHistory.ok) {
        const dataHistory = await resHistory.json();
        setLogs(dataHistory.logs);
        setTrades(dataHistory.trades);
      }

      const resSignals = await fetch(`${API_BASE}/signals`);
      if (resSignals.ok) {
        const dataSignals = await resSignals.json();
        setSignals(dataSignals);
      }
    } catch (err: any) {
      setConnected(false);
      setApiError(err.message || "Cannot connect to Python API server. Ensure server.py is running on port 8484.");
    } finally {
      setIsSignalsLoading(false);
    }
  }, []);

  useEffect(() => {
    setMounted(true);
    loadData(true);
    const intervalId = setInterval(() => loadData(false), 3000); // Fixed 3 seconds refresh (silent)
    return () => clearInterval(intervalId);
  }, [loadData]);

  useEffect(() => {
    if (!isConfigInitialized && status.trade_mode !== "") {
      setFormMode(status.trade_mode);
      const us = status.symbols.filter(s => !s.endsWith('.HK')).join(", ");
      const hk = status.symbols.filter(s => s.endsWith('.HK')).join(", ");
      setFormUsSymbols(us);
      setFormHkSymbols(hk);
      setFormQty(status.quantity);
      setFormInterval(status.interval);
      setFormPeriod(status.candle_period);
      setFormStrategy(status.strategy);
      setIsConfigInitialized(true);
    }
  }, [status, isConfigInitialized]);

  useEffect(() => {
    if (connected && status.symbols.length > 0) {
      const isAutoLoaded = localStorage.getItem("hk_auto_loaded_v1");
      if (!isAutoLoaded) {
        const recommendedList = [
          "0700.HK", "9988.HK", "1810.HK", "1211.HK", "3690.HK",
          "9618.HK", "0981.HK", "2318.HK", "0939.HK", "1398.HK",
          "3988.HK", "1024.HK", "9888.HK", "2015.HK", "9868.HK",
          "2269.HK", "2382.HK", "2628.HK", "0388.HK", "1299.HK",
          "0005.HK", "0941.HK", "0883.HK", "9999.HK", "9626.HK",
          "0992.HK", "1347.HK", "0001.HK", "0012.HK", "0016.HK",
          "0823.HK", "0960.HK", "0857.HK", "0386.HK", "1898.HK",
          "1088.HK", "1818.HK", "2899.HK", "1772.HK", "9696.HK",
          "0175.HK", "9866.HK", "2333.HK", "2359.HK", "0241.HK",
          "6618.HK", "1876.HK", "2319.HK", "2020.HK", "2331.HK",
          "6862.HK", "1928.HK", "0027.HK", "0728.HK", "0762.HK",
          "0002.HK", "0003.HK", "0006.HK", "0011.HK", "0066.HK",
          "0101.HK", "0267.HK", "0291.HK", "0322.HK", "0669.HK",
          "0688.HK", "0763.HK", "0867.HK", "0966.HK", "0968.HK",
          "1038.HK", "1044.HK", "1093.HK", "1109.HK", "1113.HK",
          "1177.HK", "1199.HK", "1378.HK", "1918.HK", "2007.HK"
        ];
        
        const missing = recommendedList.filter(sym => !status.symbols.includes(sym));
        if (missing.length > 0 && !actionLoading) {
          const autoMonitorAll = async () => {
            const updatedSymbols = [...status.symbols];
            for (const sym of recommendedList) {
              if (!updatedSymbols.includes(sym)) {
                updatedSymbols.push(sym);
              }
            }
            
            try {
              const res = await fetch(`${API_BASE}/config`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                  trade_mode: status.trade_mode,
                  symbols: updatedSymbols,
                  quantity: status.quantity,
                  quantity_hk: status.quantity_hk,
                  interval: status.interval,
                  candle_period: status.candle_period,
                  strategy: status.strategy,
                  username: "",
                  password: "",
                  trade_pin: "",
                  app_key: "",
                  app_secret: ""
                })
              });
              if (res.ok) {
                localStorage.setItem("hk_auto_loaded_v1", "true");
                setIsConfigInitialized(false);
                await loadData();
              }
            } catch (err) {
              console.error("Auto load HK symbols failed:", err);
            }
          };
          
          autoMonitorAll();
        } else {
          localStorage.setItem("hk_auto_loaded_v1", "true");
        }
      }
    }
  }, [connected, status.symbols, actionLoading, loadData]);

  const handleManualScan = async () => {
    setIsScanning(true);
    try {
      const resSignals = await fetch(`${API_BASE}/signals`);
      if (resSignals.ok) {
        const dataSignals = await resSignals.json();
        setSignals(dataSignals);
      }
    } catch (err) {
      console.error("Manual scan error:", err);
    } finally {
      setIsScanning(false);
    }
  };

  const handleToggleBot = async () => {
    setActionLoading(true);
    const endpoint = status.running ? "stop" : "start";
    try {
      const res = await fetch(`${API_BASE}/${endpoint}`, { method: "POST" });
      const data = await res.json();
      if (!res.ok) {
        showToast(`Error: ${data.detail || "Request failed"}`, "error");
      } else {
        showToast(`บอท${status.running ? 'หยุดทำงาน' : 'เริ่มทำงาน'}สำเร็จ`, "success");
        await loadData();
      }
    } catch (err) {
      showToast("Failed to toggle bot loop. Check backend console.", "error");
    } finally {
      setActionLoading(false);
    }
  };

  const handleQuickTrade = async (symbol: string, action: "BUY" | "SELL", defaultQty?: number) => {
    const startQty = defaultQty !== undefined ? defaultQty : status.quantity_hk;
    setTradeDialogSymbol(symbol);
    setTradeDialogAction(action);
    setTradeDialogDefaultQty(startQty);
    setTradeDialogOpen(true);
  };

  const handleExecuteQuickTrade = async (qtyNum: number) => {
    setTradeDialogPending(true);
    try {
      const res = await fetch(`${API_BASE}/order`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          symbol: tradeDialogSymbol,
          qty: qtyNum,
          action: tradeDialogAction,
          order_type: "MKT"
        })
      });
      
      const data = await res.json();
      if (!res.ok) {
        showToast(`ส่งออเดอร์ล้มเหลว: ${data.detail || "กรุณาตรวจสอบระบบ"}`, "error");
      } else {
        showToast(`ส่งคำสั่งซื้อขายสำเร็จ: ${tradeDialogAction} ${qtyNum} หุ้นของ ${tradeDialogSymbol}`, "success");
        await loadData();
      }
    } catch (err) {
      showToast("เกิดข้อผิดพลาดในการเชื่อมต่อเครือข่าย", "error");
    } finally {
      setTradeDialogPending(false);
      setTradeDialogOpen(false);
    }
  };

  const handleSaveConfig = async (e: React.FormEvent) => {
    e.preventDefault();
    setActionLoading(true);
    
    const usList = formUsSymbols
      .split(",")
      .map(s => s.trim().toUpperCase())
      .filter(s => s.length > 0);
      
    const hkList = formHkSymbols
      .split(",")
      .map(s => {
        let sym = s.trim().toUpperCase();
        if (sym.length > 0 && !sym.endsWith(".HK")) {
          sym += ".HK";
        }
        return sym;
      })
      .filter(s => s.length > 0);
      
    const combinedSymbols = [...usList, ...hkList];

    try {
      const res = await fetch(`${API_BASE}/config`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          trade_mode: formMode,
          symbols: combinedSymbols,
          quantity: formQty,
          interval: formInterval,
          candle_period: formPeriod,
          strategy: formStrategy,
          username: formUsername,
          password: formPassword,
          trade_pin: formTradePin,
          app_key: formAppKey,
          app_secret: formAppSecret
        })
      });

      const data = await res.json();
      if (!res.ok) {
        showToast(`Config Save Error: ${data.detail || "Validation failed"}`, "error");
      } else {
        showToast("บันทึกการตั้งค่าระบบเรียบร้อยแล้ว!", "success");
        setIsConfigInitialized(false); // Unlock to fetch updated server values
        setFormUsername("");
        setFormPassword("");
        setFormTradePin("");
        setFormAppKey("");
        setFormAppSecret("");
        await loadData();
      }
    } catch (err) {
      showToast("Failed to update config. Backend might be reinitializing.", "error");
    } finally {
      setActionLoading(false);
    }
  };

  const handleAddRecommendedSymbol = async (symbol: string) => {
    if (status.symbols.includes(symbol)) {
      showToast(`มีรหัส ${symbol} อยู่ในสแกนเนอร์บอทแล้วครับ`, "warning");
      return;
    }
    setActionLoading(true);
    const updatedSymbols = [...status.symbols, symbol];
    try {
      const res = await fetch(`${API_BASE}/config`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          trade_mode: status.trade_mode,
          symbols: updatedSymbols,
          quantity: status.quantity,
          quantity_hk: status.quantity_hk,
          interval: status.interval,
          candle_period: status.candle_period,
          strategy: status.strategy,
          username: "",
          password: "",
          trade_pin: "",
          app_key: "",
          app_secret: ""
        })
      });
      if (res.ok) {
        showToast(`เพิ่ม ${symbol} เข้า Watchlist และรีสตาร์ทบอทสำเร็จ!`, "success");
        setIsConfigInitialized(false);
        await loadData(true);
      } else {
        const data = await res.json();
        showToast(`ล้มเหลว: ${data.detail || "ข้อผิดพลาดระบบหลังบ้าน"}`, "error");
      }
    } catch (err) {
      showToast("เชื่อมต่อหลังบ้านล้มเหลว", "error");
    } finally {
      setActionLoading(false);
    }
  };

  const handleMonitorAllRecommended = async () => {
    setActionLoading(true);
    const recommendedList = [
      "0700.HK", "9988.HK", "1810.HK", "1211.HK", "3690.HK",
      "9618.HK", "0981.HK", "2318.HK", "0939.HK", "1398.HK",
      "3988.HK", "1024.HK", "9888.HK", "2015.HK", "9868.HK",
      "2269.HK", "2382.HK", "2628.HK", "0388.HK", "1299.HK",
      "0005.HK", "0941.HK", "0883.HK", "9999.HK", "9626.HK",
      "0992.HK", "1347.HK", "0001.HK", "0012.HK", "0016.HK",
      "0823.HK", "0960.HK", "0857.HK", "0386.HK", "1898.HK",
      "1088.HK", "1818.HK", "2899.HK", "1772.HK", "9696.HK",
      "0175.HK", "9866.HK", "2333.HK", "2359.HK", "0241.HK",
      "6618.HK", "1876.HK", "2319.HK", "2020.HK", "2331.HK",
      "6862.HK", "1928.HK", "0027.HK", "0728.HK", "0762.HK",
      "0002.HK", "0003.HK", "0006.HK", "0011.HK", "0066.HK",
      "0101.HK", "0267.HK", "0291.HK", "0322.HK", "0669.HK",
      "0688.HK", "0763.HK", "0867.HK", "0966.HK", "0968.HK",
      "1038.HK", "1044.HK", "1093.HK", "1109.HK", "1113.HK",
      "1177.HK", "1199.HK", "1378.HK", "1918.HK", "2007.HK"
    ];
    
    const updatedSymbols = [...status.symbols];
    let addedCount = 0;
    for (const sym of recommendedList) {
      if (!updatedSymbols.includes(sym)) {
        updatedSymbols.push(sym);
        addedCount++;
      }
    }
    
    if (addedCount === 0) {
      showToast("มีหุ้นแนะนำทั้งหมดอยู่ในระบบสแกนเนอร์บอทเรียบร้อยแล้วครับ!", "info");
      setActionLoading(false);
      return;
    }
    
    try {
      const res = await fetch(`${API_BASE}/config`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          trade_mode: status.trade_mode,
          symbols: updatedSymbols,
          quantity: status.quantity,
          quantity_hk: status.quantity_hk,
          interval: status.interval,
          candle_period: status.candle_period,
          strategy: status.strategy,
          username: "",
          password: "",
          trade_pin: "",
          app_key: "",
          app_secret: ""
        })
      });
      if (res.ok) {
        showToast("เพิ่มหุ้นแนะนำทั้งหมดเข้าสแกนเนอร์บอทและรีสตาร์ทสำเร็จ!", "success");
        setIsConfigInitialized(false);
        const newHkSymbols = updatedSymbols.filter(s => s.endsWith('.HK'));
        setDrawerHkSymbols(newHkSymbols);
        await loadData(true);
      } else {
        const data = await res.json();
        showToast(`ล้มเหลว: ${data.detail || "ข้อผิดพลาดระบบหลังบ้าน"}`, "error");
      }
    } catch (err) {
      showToast("เชื่อมต่อหลังบ้านล้มเหลว", "error");
    } finally {
      setActionLoading(false);
    }
  };

  const isProfit = balance.unrealized_pnl >= 0;
  const pnlPercent = balance.net_liquidation > 0 
    ? (balance.unrealized_pnl / (balance.net_liquidation - balance.unrealized_pnl)) * 100 
    : 0;

  const filteredSignals = signals.filter(sig => {
    const isMarketMatch = marketTab === 1 ? sig.symbol.endsWith('.HK') : !sig.symbol.endsWith('.HK');
    if (!isMarketMatch) return false;
    if (maxPrice !== "") {
      const priceNum = parseFloat(maxPrice);
      if (!isNaN(priceNum)) {
        if (priceOperator === "ge" && sig.price < priceNum) return false;
        if (priceOperator === "le" && sig.price > priceNum) return false;
      }
    }
    return true;
  });

  return (
    <>

        {/* 2. Top Metric Cards Panel */}
        <Box 
          sx={{ 
            display: 'grid', 
            gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr', md: '1fr 1fr 1fr 1fr' }, 
            gap: 3, 
            mb: 4 
          }}
        >
          {/* Card 1: Available Cash */}
          <Card>
            <CardContent sx={{ position: 'relative', overflow: 'hidden' }}>
              <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 1.5 }}>
                <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600, letterSpacing: '0.5px' }}>
                  ยอดเงินสดคงเหลือ
                </Typography>
                <Box sx={{ p: 1, borderRadius: '10px', bgcolor: 'rgba(59, 130, 246, 0.08)', display: 'flex' }}>
                  <Wallet size={18} color="#3b82f6" />
                </Box>
              </Box>
              <Typography variant="h4" sx={{ fontWeight: 800, fontFamily: 'var(--font-mono)', mb: 0.5 }}>
                ${balance.cash.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </Typography>
              <Typography variant="caption" color="text.secondary" sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                <Database size={10} /> สกุลเงิน: {balance.currency}
              </Typography>
            </CardContent>
          </Card>

          {/* Card 2: Net Liquidation */}
          <Card>
            <CardContent>
              <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 1.5 }}>
                <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600, letterSpacing: '0.5px' }}>
                  มูลค่าพอร์ตรวม
                </Typography>
                <Box sx={{ p: 1, borderRadius: '10px', bgcolor: 'rgba(59, 130, 246, 0.08)', display: 'flex' }}>
                  <TrendingUp size={18} color="#3b82f6" />
                </Box>
              </Box>
              <Typography variant="h4" sx={{ fontWeight: 800, fontFamily: 'var(--font-mono)', mb: 0.5 }}>
                ${balance.net_liquidation.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                เงินสด + มูลค่าตลาดของหุ้นที่ถือครอง
              </Typography>
            </CardContent>
          </Card>

          {/* Card 3: Unrealized Profit & Loss */}
          <Card>
            <CardContent>
              <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 1.5 }}>
                <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600, letterSpacing: '0.5px' }}>
                  กำไร/ขาดทุนสะสม
                </Typography>
                <Box sx={{ p: 1, borderRadius: '10px', bgcolor: isProfit ? 'rgba(16, 185, 129, 0.08)' : 'rgba(244, 63, 94, 0.08)', display: 'flex' }}>
                  {isProfit ? <TrendingUp size={18} color="#10b981" /> : <TrendingDown size={18} color="#f43f5e" />}
                </Box>
              </Box>
              <Typography 
                variant="h4" 
                color={isProfit ? "success.main" : "error.main"}
                sx={{ fontWeight: 800, fontFamily: 'var(--font-mono)', mb: 0.5 }}
              >
                {isProfit ? "+" : ""}${balance.unrealized_pnl.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </Typography>
              <Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
                <Chip 
                  label={`${isProfit ? "+" : ""}${pnlPercent.toFixed(2)}%`}
                  size="small"
                  color={isProfit ? "success" : "error"}
                  sx={{ height: 18, fontSize: '0.7rem', fontWeight: 700, borderRadius: '6px' }}
                />
                <Typography variant="caption" color="text.secondary">
                  จากเงินลงทุนทั้งหมด
                </Typography>
              </Box>
            </CardContent>
          </Card>

          {/* Card 4: Bot status toggle control */}
          <Card sx={{ borderLeft: `2px solid ${status.running ? '#10b981' : '#64748b'}` }}>
            <CardContent>
              <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 1.5 }}>
                <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600, letterSpacing: '0.5px' }}>
                  สถานะการทำงานบอท
                </Typography>
                <Box sx={{ p: 1, borderRadius: '10px', bgcolor: status.running ? 'rgba(16, 185, 129, 0.08)' : 'rgba(100, 116, 139, 0.08)', display: 'flex' }}>
                  <Activity size={18} color={status.running ? "#10b981" : "#64748b"} />
                </Box>
              </Box>
              <Typography 
                variant="h4" 
                color={status.running ? "success.main" : "text.secondary"}
                sx={{ fontWeight: 800, mb: 0.5 }}
              >
                {status.running ? "RUNNING" : "STANDBY"}
              </Typography>
              
              <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mt: 0.5 }}>
                <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 500 }}>
                  กลยุทธ์: {status.strategy.toUpperCase()}
                </Typography>
                
                <FormControlLabel
                  control={
                    <Switch 
                      checked={status.running} 
                      onChange={handleToggleBot}
                      color="success"
                      disabled={actionLoading || !connected}
                      size="small"
                    />
                  }
                  label=""
                  sx={{ mr: 0 }}
                />
              </Box>
            </CardContent>
          </Card>
        </Box>

        {/* 3. Main Body Container (Vertical Stack) */}
        <Box sx={{ display: "flex", flexDirection: "column", gap: 3 }}>
          
          {/* Real-time Signals Scanner */}
          <Card>
            <CardContent sx={{ p: 0, '&:last-child': { pb: 0 } }}>
              <Box sx={{ p: 3, display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: 'wrap', gap: 2 }}>
                <Box sx={{ display: "flex", alignItems: "center", gap: 1.5 }}>
                  <Box sx={{ p: 1, borderRadius: '10px', bgcolor: 'rgba(59, 130, 246, 0.06)', display: 'flex' }}>
                    <Eye size={18} color="#3b82f6" />
                  </Box>
                  <Box>
                    <Typography variant="h6" sx={{ fontWeight: 700 }}>
                      สแกนเนอร์สัญญาณเทรดเรียลไทม์ (Real-time Trading Signals)
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      วิเคราะห์ราคาปัจจุบันและประเมินทิศทางแนวโน้มตามอินดิเคเตอร์ทางเทคนิค
                    </Typography>
                  </Box>
                </Box>

                {/* Scan Controls like metabot */}
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <FormControl size="small" sx={{ width: 65 }}>
                    <Select
                      value={priceOperator}
                      onChange={(e) => {
                        setPriceOperator(e.target.value as "le" | "ge");
                        setPage(0);
                      }}
                      sx={{ 
                        borderRadius: '8px 0 0 8px',
                        bgcolor: 'rgba(255,255,255,0.02)',
                        '& .MuiOutlinedInput-notchedOutline': {
                          borderRight: 'none'
                        }
                      }}
                    >
                      <MenuItem value="ge">≥</MenuItem>
                      <MenuItem value="le">≤</MenuItem>
                    </Select>
                  </FormControl>
                  <TextField
                    size="small"
                    label="ราคา (Price)"
                    type="number"
                    value={maxPrice}
                    onChange={(e) => {
                      setMaxPrice(e.target.value);
                      setPage(0);
                    }}
                    placeholder="ทั้งหมด"
                    slotProps={{
                      htmlInput: { min: 0, step: 1 },
                      inputLabel: { shrink: true }
                    }}
                    sx={{ 
                      width: 110,
                      mr: 1.5,
                      '& .MuiOutlinedInput-root': {
                        borderRadius: '0 8px 8px 0',
                        bgcolor: 'rgba(255,255,255,0.02)'
                      }
                    }}
                  />
                  <Button
                    variant="outlined"
                    color="primary"
                    size="small"
                    disabled={actionLoading || !connected}
                    onClick={handleOpenDrawer}
                    startIcon={<ListPlus size={16} />}
                    sx={{ 
                      height: 34, 
                      borderRadius: '8px', 
                      fontSize: '0.78rem',
                      px: 2,
                      mr: 1.5,
                      borderColor: 'rgba(59, 130, 246, 0.4)',
                      color: '#3b82f6',
                      '&:hover': {
                        borderColor: '#3b82f6',
                        bgcolor: 'rgba(59, 130, 246, 0.05)'
                      }
                    }}
                  >
                    จัดการรายการหุ้น (Watchlist)
                  </Button>

                  <Button
                    variant="contained"
                    color="secondary"
                    size="small"
                    disabled={isScanning || actionLoading || !connected}
                    onClick={handleManualScan}
                    sx={{ 
                      height: 34, 
                      borderRadius: '8px', 
                      fontSize: '0.78rem',
                      px: 2
                    }}
                  >
                    {isScanning ? (
                      <RefreshCw size={14} className="spin" />
                    ) : (
                      "สแกนสดทันที (Scan Now)"
                    )}
                  </Button>
                </Box>
              </Box>
              
              <Box sx={{ px: 3, pb: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 1 }}>
                <Typography variant="caption" sx={{ color: 'text.secondary', fontWeight: 500 }}>
                  📊 กำลังแสดง <span style={{ color: '#3b82f6', fontWeight: 700 }}>{filteredSignals.length}</span> จากทั้งหมด <span style={{ fontWeight: 600 }}>{signals.filter(s => s.symbol.endsWith('.HK')).length}</span> หุ้นฮ่องกงในระบบสแกนเนอร์
                </Typography>
                {maxPrice && (
                  <Typography variant="caption" sx={{ color: 'success.main', fontWeight: 600, bgcolor: 'rgba(16, 185, 129, 0.08)', px: 1.5, py: 0.4, borderRadius: '6px', border: '1px solid rgba(16, 185, 129, 0.15)' }}>
                    คัดกรอง: ราคา {priceOperator === 'ge' ? '≥' : '≤'} {maxPrice} HKD
                  </Typography>
                )}
              </Box>

              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell sx={{ width: '28%' }}>หุ้น / บริษัท (Ticker & Company)</TableCell>
                      <TableCell align="right" sx={{ width: '12%' }}>ราคาล่าสุด</TableCell>
                      <TableCell align="left" sx={{ pl: 4, width: '25%' }}>ตัวชี้วัดทางเทคนิค (Technical Indicators)</TableCell>
                      <TableCell align="center" sx={{ width: '20%' }}>ความสอดคล้องสัญญาณ (Confluence)</TableCell>
                      <TableCell align="center" sx={{ width: '15%' }}>ซื้อขายด่วน (Quick Trade)</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {isSignalsLoading && filteredSignals.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={5} align="center" sx={{ py: 6 }}>
                          <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 1.5, py: 2 }}>
                            <CircularProgress size={24} color="primary" />
                            <Typography variant="body2" color="text.secondary">กำลังโหลดสัญญาณทางเทคนิคเรียลไทม์...</Typography>
                          </Box>
                        </TableCell>
                      </TableRow>
                    ) : filteredSignals.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={5} align="center" sx={{ py: 6, color: 'text.secondary' }}>
                          {connected ? "ไม่มีข้อมูลหุ้นในระดับราคาที่เลือกขณะนี้" : "เซิร์ฟเวอร์ออฟไลน์ ไม่สามารถดึงข้อมูลสัญญาณได้"}
                        </TableCell>
                      </TableRow>
                    ) : (
                      filteredSignals
                        .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
                        .map((sig) => {
                          const getConfluenceSignal = (smaSig: string, rsiSig: string, hybridSig: string) => {
                            let score = 0;
                            const parseVal = (sig: string) => {
                              if (sig === "BUY") return 1;
                              if (sig === "SELL") return -1;
                              return 0;
                            };
                            score += parseVal(smaSig);
                            score += parseVal(rsiSig);
                            score += parseVal(hybridSig);
                            
                            if (score === 3) {
                              return { label: "100% BUY", desc: "มติเอกฉันท์ซื้อ (3/3)", bgcolor: 'rgba(22, 199, 132, 0.15)', textcolor: '#16c784', border: '1px solid #16c784' };
                            } else if (score === 2) {
                              return { label: "67% BUY", desc: "แนวโน้มซื้อแข็งแกร่ง (2/3)", bgcolor: 'rgba(22, 199, 132, 0.08)', textcolor: '#16c784', border: '1px dashed rgba(22, 199, 132, 0.5)' };
                            } else if (score === 1) {
                              return { label: "33% BUY", desc: "สัญญาณซื้ออ่อน (1/3)", bgcolor: 'transparent', textcolor: '#16c784', border: '1px solid rgba(22, 199, 132, 0.25)' };
                            } else if (score === -3) {
                              return { label: "100% SELL", desc: "มติเอกฉันท์ขาย (3/3)", bgcolor: 'rgba(234, 57, 67, 0.15)', textcolor: '#ea3943', border: '1px solid #ea3943' };
                            } else if (score === -2) {
                              return { label: "67% SELL", desc: "แนวโน้มขายแข็งแกร่ง (2/3)", bgcolor: 'rgba(234, 57, 67, 0.08)', textcolor: '#ea3943', border: '1px dashed rgba(234, 57, 67, 0.5)' };
                            } else if (score === -1) {
                              return { label: "33% SELL", desc: "สัญญาณขายอ่อน (1/3)", bgcolor: 'transparent', textcolor: '#ea3943', border: '1px solid rgba(234, 57, 67, 0.25)' };
                            } else {
                              return { label: "NEUTRAL / HOLD", desc: "ไม่มีทิศทางชัดเจน (0/3)", bgcolor: 'rgba(148, 163, 184, 0.05)', textcolor: '#94a3b8', border: '1px solid rgba(148, 163, 184, 0.15)' };
                            }
                          };
                          
                          const conf = getConfluenceSignal(sig.sma_signal, sig.rsi_signal, sig.hybrid_signal);
                          
                          return (
                            <TableRow key={sig.symbol} hover sx={{ '&:hover': { bgcolor: 'rgba(255,255,255,0.02)' } }}>
                              <TableCell sx={{ py: 1.5 }}>
                                <Typography sx={{ fontWeight: 800, color: 'primary.main', fontSize: '0.9rem', lineHeight: 1.1 }}>
                                  {sig.symbol}
                                </Typography>
                                <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.72rem', display: 'block', mt: 0.2 }}>
                                  {STOCK_NAMES[sig.symbol] || (sig.symbol.endsWith('.HK') ? "Hong Kong Listed Company" : "US Listed Company")}
                                </Typography>
                              </TableCell>
                              <TableCell align="right" sx={{ fontFamily: 'var(--font-mono)', fontWeight: 600, py: 1.5 }}>
                                ${sig.price > 0 ? sig.price.toFixed(2) : "N/A"}
                              </TableCell>
                              <TableCell align="left" sx={{ py: 1.5, pl: 4 }}>
                                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.3 }}>
                                  <Typography variant="body2" sx={{ fontSize: '0.8rem', display: 'flex', alignItems: 'center', gap: 1 }}>
                                    <span style={{ color: '#94a3b8', fontWeight: 600 }}>RSI (14):</span>
                                    <span style={{ 
                                      color: sig.rsi > 60 ? '#ea3943' : sig.rsi < 40 ? '#16c784' : '#94a3b8',
                                      fontWeight: (sig.rsi > 60 || sig.rsi < 40) ? 700 : 500
                                    }}>
                                      {sig.rsi > 0 ? sig.rsi.toFixed(1) : "N/A"}
                                    </span>
                                  </Typography>
                                  <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)' }}>
                                    SMA(10/30): {sig.sma_fast > 0 ? `$${sig.sma_fast.toFixed(2)} / $${sig.sma_slow.toFixed(2)}` : "N/A"}
                                  </Typography>
                                </Box>
                              </TableCell>
                              <TableCell align="center" sx={{ py: 1.5 }}>
                                <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 0.5 }}>
                                  <Box sx={{ 
                                    display: 'inline-block',
                                    px: 1.5,
                                    py: 0.5,
                                    borderRadius: '6px',
                                    bgcolor: conf.bgcolor,
                                    color: conf.textcolor,
                                    border: conf.border,
                                    fontWeight: 800,
                                    fontSize: '0.75rem',
                                    letterSpacing: '0.02em',
                                    boxShadow: conf.label.includes("100%") 
                                      ? `0 0 12px ${conf.textcolor}20` 
                                      : 'none'
                                  }}>
                                    {conf.label}
                                  </Box>
                                  <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.68rem', fontWeight: 500 }}>
                                    {conf.desc}
                                  </Typography>
                                </Box>
                              </TableCell>
                              <TableCell align="center" sx={{ py: 1.5 }}>
                                <Box sx={{ display: 'flex', gap: 1, justifyContent: 'center' }}>
                                  <Button
                                    variant="contained"
                                    color="success"
                                    size="small"
                                    onClick={() => handleQuickTrade(sig.symbol, "BUY")}
                                    disabled={actionLoading || !status.has_client || !connected}
                                    sx={{ 
                                      minWidth: 50, 
                                      height: 28, 
                                      fontSize: '0.72rem', 
                                      borderRadius: '6px',
                                      boxShadow: 'none',
                                      '&:hover': { bgcolor: '#10b981' }
                                    }}
                                  >
                                    BUY
                                  </Button>
                                  <Button
                                    variant="contained"
                                    color="error"
                                    size="small"
                                    onClick={() => handleQuickTrade(sig.symbol, "SELL")}
                                    disabled={actionLoading || !status.has_client || !connected}
                                    sx={{ 
                                      minWidth: 50, 
                                      height: 28, 
                                      fontSize: '0.72rem', 
                                      borderRadius: '6px',
                                      boxShadow: 'none',
                                      '&:hover': { bgcolor: '#ea3943' }
                                    }}
                                  >
                                    SELL
                                  </Button>
                                </Box>
                              </TableCell>
                            </TableRow>
                          );
                        })
                    )}
                  </TableBody>
                </Table>
              </TableContainer>

                <TablePagination
                  rowsPerPageOptions={[5, 10, 20, 50, 100]}
                  component="div"
                  count={filteredSignals.length}
                  rowsPerPage={rowsPerPage}
                  page={page}
                  onPageChange={(_, newPage) => setPage(newPage)}
                  onRowsPerPageChange={(e) => {
                    setRowsPerPage(parseInt(e.target.value, 10));
                    setPage(0);
                  }}
                  sx={{
                    borderTop: '1px solid rgba(255, 255, 255, 0.05)',
                    color: 'text.secondary',
                    '.MuiTablePagination-selectIcon': {
                      color: 'text.secondary'
                    }
                  }}
                />
              </CardContent>
            </Card>

            {/* Positions Table */}
            <Card>
              <CardContent sx={{ p: 0, '&:last-child': { pb: 0 } }}>
                <Box sx={{ p: 3, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <Box sx={{ display: "flex", alignItems: "center", gap: 1.5 }}>
                    <Box sx={{ p: 1, borderRadius: '10px', bgcolor: 'rgba(59, 130, 246, 0.06)', display: 'flex' }}>
                      <Activity size={18} color="#3b82f6" />
                    </Box>
                    <Box>
                      <Typography variant="h6" sx={{ fontWeight: 700 }}>
                        หุ้นในพอร์ต (Active Positions)
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        สัญญาสมการครองชีพของหลักทรัพย์ที่ถืออยู่ในพอร์ตโฟลิโอขณะนี้
                      </Typography>
                    </Box>
                  </Box>
                </Box>
                
                <TableContainer>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>หุ้น (Ticker)</TableCell>
                        <TableCell align="right">จำนวนหุ้น (Shares)</TableCell>
                        <TableCell align="right">ทุนเฉลี่ย (Avg Price)</TableCell>
                        <TableCell align="right">มูลค่าตลาด (Market Value)</TableCell>
                        <TableCell align="right">กำไร / ขาดทุน (P&L)</TableCell>
                        <TableCell align="center">แอ็กชัน (Action)</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {positions.filter(pos => marketTab === 1 ? pos.symbol.endsWith('.HK') : !pos.symbol.endsWith('.HK')).length === 0 ? (
                        <TableRow>
                          <TableCell colSpan={6} align="center" sx={{ py: 8, color: 'text.secondary' }}>
                            ไม่มีหุ้นถือครองอยู่ในพอร์ตโฟลิโอสำหรับตลาดนี้ขณะนี้
                          </TableCell>
                        </TableRow>
                      ) : (
                        positions
                          .filter(pos => marketTab === 1 ? pos.symbol.endsWith('.HK') : !pos.symbol.endsWith('.HK'))
                          .map((pos) => {
                          const posProfit = pos.unrealized_pnl >= 0;
                          return (
                            <TableRow key={pos.symbol} hover sx={{ '&:hover': { bgcolor: 'rgba(255,255,255,0.02)' } }}>
                              <TableCell sx={{ py: 1.5 }}>
                                <Typography sx={{ fontWeight: 800, color: 'primary.main', fontSize: '0.9rem', lineHeight: 1.1 }}>
                                  {pos.symbol}
                                </Typography>
                                <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.72rem', display: 'block', mt: 0.2 }}>
                                   {STOCK_NAMES[pos.symbol] || (pos.symbol.endsWith('.HK') ? "Hong Kong Listed Company" : "US Listed Company")}
                                </Typography>
                              </TableCell>
                              <TableCell align="right" sx={{ fontFamily: 'var(--font-mono)', fontWeight: 600 }}>{pos.qty}</TableCell>
                              <TableCell align="right" sx={{ fontFamily: 'var(--font-mono)' }}>${pos.avg_price.toFixed(2)}</TableCell>
                              <TableCell align="right" sx={{ fontFamily: 'var(--font-mono)' }}>${pos.market_value.toFixed(2)}</TableCell>
                              <TableCell align="right">
                                <Box sx={{ display: "flex", justifyContent: "flex-end", alignItems: "center", gap: 1 }}>
                                  <Typography 
                                    sx={{ 
                                      color: posProfit ? 'success.main' : 'error.main',
                                      fontWeight: 700,
                                      fontFamily: 'var(--font-mono)'
                                    }}
                                  >
                                    {posProfit ? "+" : ""}${pos.unrealized_pnl.toFixed(2)}
                                  </Typography>
                                  <Chip 
                                    label={pos.avg_price > 0 ? `${(pos.unrealized_pnl / (pos.avg_price * pos.qty) * 100).toFixed(2)}%` : "0%"}
                                    size="small"
                                    color={posProfit ? "success" : "error"}
                                    variant="outlined"
                                    sx={{ height: 16, fontSize: '0.65rem', fontWeight: 600, px: 0.2 }}
                                  />
                                </Box>
                              </TableCell>
                              <TableCell align="center">
                                <Button
                                  variant="contained"
                                  color="error"
                                  size="small"
                                  onClick={() => handleQuickTrade(pos.symbol, "SELL", pos.qty)}
                                  disabled={actionLoading || !status.has_client || !connected}
                                  sx={{ 
                                    minWidth: 60, 
                                    height: 28, 
                                    fontSize: '0.72rem', 
                                    borderRadius: '6px',
                                    boxShadow: 'none',
                                    '&:hover': { bgcolor: '#ea3943' }
                                  }}
                                >
                                  SELL
                                </Button>
                              </TableCell>
                            </TableRow>
                          );
                        })
                      )}
                    </TableBody>
                  </Table>
                </TableContainer>
              </CardContent>
            </Card>
        </Box>

      <Drawer
        anchor="right"
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
      >
        <Box
          sx={{
            width: { xs: '100vw', sm: 500 },
            height: '100%',
            bgcolor: '#0f141c',
            borderLeft: '1px solid rgba(255, 255, 255, 0.08)',
            p: 3,
            display: 'flex',
            flexDirection: 'column',
            gap: 3,
            boxSizing: 'border-box'
          }}
        >
          {/* Drawer Header */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <ListPlus size={20} color="#3b82f6" />
            <Typography variant="h6" sx={{ fontWeight: 800 }}>
              จัดการรายการหุ้นฮ่องกง
            </Typography>
          </Box>
          <IconButton onClick={() => setDrawerOpen(false)} size="small" sx={{ color: 'text.secondary' }}>
            <X size={18} />
          </IconButton>
        </Box>

        <Divider sx={{ borderColor: 'rgba(255, 255, 255, 0.06)' }} />

        {/* Section 1: Add New Ticker */}
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
          <Typography variant="subtitle2" sx={{ fontWeight: 700, color: 'text.primary' }}>
            ➕ เพิ่มหุ้นตัวใหม่ (Add Ticker)
          </Typography>
          <Box 
            component="form" 
            onSubmit={(e) => {
              e.preventDefault();
              handleAddSymbol(newSymbolInput);
            }}
            sx={{ display: 'flex', gap: 1 }}
          >
            <TextField
              size="small"
              fullWidth
              placeholder="เช่น 0700 หรือ 0005.HK"
              value={newSymbolInput}
              onChange={(e) => setNewSymbolInput(e.target.value)}
              sx={{
                '& .MuiOutlinedInput-root': {
                  borderRadius: '8px',
                  bgcolor: 'rgba(255,255,255,0.02)'
                }
              }}
            />
            <Button
              variant="contained"
              color="primary"
              type="submit"
              sx={{ borderRadius: '8px', minWidth: 60 }}
            >
              เพิ่ม
            </Button>
          </Box>
        </Box>

        {/* Section 2: Recommended Stocks */}
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="subtitle2" sx={{ fontWeight: 700, color: 'text.primary' }}>
              ⭐ หุ้นฮ่องกงแนะนำ (Recommended)
            </Typography>
            <Button
              size="small"
              variant="text"
              color="primary"
              onClick={handleMonitorAllRecommended}
              disabled={actionLoading}
              sx={{ 
                fontSize: '0.72rem', 
                py: 0, 
                fontWeight: 700,
                display: 'flex',
                alignItems: 'center',
                gap: 0.5
              }}
            >
              {actionLoading ? (
                <>
                  <CircularProgress size={12} sx={{ color: 'primary.main' }} />
                  กำลังดำเนินการ...
                </>
              ) : (
                "เพิ่มทั้งหมด 80 ตัว"
              )}
            </Button>
          </Box>
          <Typography variant="caption" color="text.secondary">คลิกเลือกทีละตัวด้านล่าง หรือกด "เพิ่มทั้งหมด 80 ตัว" เพื่อสแกนตลาดฮ่องกงแบบครอบคลุม</Typography>
          <Box sx={{ 
            maxHeight: 120, 
            overflowY: 'auto', 
            display: 'flex', 
            gap: 0.8, 
            flexWrap: 'wrap', 
            p: 1, 
            bgcolor: 'rgba(255,255,255,0.01)', 
            borderRadius: '8px',
            border: '1px solid rgba(255,255,255,0.04)'
          }}>
            {[
              "0700.HK", "9988.HK", "1810.HK", "1211.HK", "3690.HK",
              "9618.HK", "0981.HK", "2318.HK", "0939.HK", "1398.HK",
              "3988.HK", "1024.HK", "9888.HK", "2015.HK", "9868.HK",
              "2269.HK", "2382.HK", "2628.HK", "0388.HK", "1299.HK"
            ]
              .filter(sym => !drawerHkSymbols.includes(sym))
              .map((sym) => (
                <Chip
                  key={sym}
                  label={`${sym.replace('.HK', '')} (${STOCK_NAMES[sym]?.split(' ')[0] || ''})`}
                  size="small"
                  onClick={() => handleAddSymbol(sym)}
                  icon={<Plus size={12} />}
                  clickable
                  sx={{ 
                    bgcolor: 'rgba(59, 130, 246, 0.08)',
                    color: '#3b82f6',
                    border: '1px solid rgba(59, 130, 246, 0.15)',
                    fontSize: '0.7rem',
                    '&:hover': {
                      bgcolor: 'rgba(59, 130, 246, 0.15)',
                    }
                  }}
                />
              ))}
            {[
              "0700.HK", "9988.HK", "1810.HK", "1211.HK", "3690.HK",
              "9618.HK", "0981.HK", "2318.HK", "0939.HK", "1398.HK",
              "3988.HK", "1024.HK", "9888.HK", "2015.HK", "9868.HK",
              "2269.HK", "2382.HK", "2628.HK", "0388.HK", "1299.HK"
            ].filter(sym => !drawerHkSymbols.includes(sym)).length === 0 && (
              <Typography variant="caption" color="text.secondary">เพิ่มหุ้นแนะนำครบทั้งหมดแล้ว</Typography>
            )}
          </Box>
        </Box>

        {/* Section 3: Current Watchlist List */}
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1, flex: 1, overflow: 'hidden' }}>
          <Typography variant="subtitle2" sx={{ fontWeight: 700, color: 'text.primary', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span>📋 รายการหุ้นสแกนปัจจุบัน ({drawerHkSymbols.length} ตัว)</span>
            {drawerHkSymbols.length > 0 && (
              <Button 
                size="small" 
                color="error" 
                variant="text" 
                onClick={() => setConfirmClearOpen(true)}
                sx={{ fontSize: '0.68rem', py: 0 }}
              >
                ล้างทั้งหมด
              </Button>
            )}
          </Typography>
          <Box sx={{ 
            flex: 1, 
            overflowY: 'auto', 
            border: '1px solid rgba(255,255,255,0.05)', 
            borderRadius: '8px',
            bgcolor: 'rgba(255,255,255,0.01)'
          }}>
            {drawerHkSymbols.length === 0 ? (
              <Box sx={{ p: 3, textAlign: 'center' }}>
                <Typography variant="caption" color="text.secondary">ไม่มีรายการหุ้นในรายการสแกนขณะนี้</Typography>
              </Box>
            ) : (
              <List dense disablePadding>
                {drawerHkSymbols.map((sym) => (
                  <ListItem 
                    key={sym} 
                    divider 
                    sx={{ 
                      py: 1,
                      px: 2,
                      borderColor: 'rgba(255, 255, 255, 0.04)',
                      '&:last-child': { borderBottom: 'none' }
                    }}
                  >
                    <ListItemText
                      primary={
                        <Typography sx={{ fontWeight: 700, fontSize: '0.85rem', color: 'primary.main' }}>
                          {sym}
                        </Typography>
                      }
                      secondary={
                        <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.68rem', display: 'block', mt: 0.2 }}>
                          {STOCK_NAMES[sym] || (sym.endsWith('.HK') ? "Hong Kong Listed Company" : "US Listed Company")}
                        </Typography>
                      }
                    />
                    <ListItemSecondaryAction>
                      <IconButton 
                        edge="end" 
                        size="small" 
                        color="error" 
                        onClick={() => handleRemoveSymbol(sym)}
                        sx={{ opacity: 0.6, '&:hover': { opacity: 1 } }}
                      >
                        <Trash2 size={16} />
                      </IconButton>
                    </ListItemSecondaryAction>
                  </ListItem>
                ))}
              </List>
            )}
          </Box>
        </Box>

        {/* Drawer Bottom Actions */}
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5, mt: 'auto', pt: 2, borderTop: '1px solid rgba(255, 255, 255, 0.06)' }}>
          <Button
            variant="contained"
            color="primary"
            fullWidth
            onClick={handleSaveDrawerConfig}
            disabled={actionLoading}
            sx={{ py: 1.2, fontWeight: 700, borderRadius: '8px' }}
          >
            {actionLoading ? <RefreshCw className="spin" size={18} /> : "บันทึก & รีโหลดบอท (Save & Hot-Reload)"}
          </Button>
          <Typography variant="caption" color="text.secondary" align="center">
            * การกดบันทึกจะเขียนทับการตั้งค่าบอทและรีสตาร์ทบอทเพื่อรับค่าใหม่ทันที
          </Typography>
        </Box>
      </Box>
    </Drawer>

    {/* Confirm Clear Watchlist Dialog */}
    <ConfirmDialog
      open={confirmClearOpen}
      title="ยืนยันการล้างรายการสแกน?"
      message="คุณต้องการลบรายชื่อหุ้นทั้งหมดในรายการสแกนนี้ใช่หรือไม่?"
      confirmText="ใช่, ล้างทั้งหมด"
      cancelText="ยกเลิก"
      severity="warning"
      loading={clearPending}
      onConfirm={handleClearAllSymbols}
      onCancel={() => setConfirmClearOpen(false)}
    />

    {/* Quick Trade Dialog */}
    <TradeDialog
      open={tradeDialogOpen}
      symbol={tradeDialogSymbol}
      action={tradeDialogAction}
      defaultQty={tradeDialogDefaultQty}
      loading={tradeDialogPending}
      onConfirm={handleExecuteQuickTrade}
      onCancel={() => setTradeDialogOpen(false)}
    />
        
    </>
  );
}
