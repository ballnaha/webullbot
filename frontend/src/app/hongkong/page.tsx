"use client";

import { useState, useEffect, useCallback, useMemo } from "react";
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
  InputAdornment,
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
  IconButton,
  Tooltip
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
  Clock,
  ArrowUpRight, 
  ArrowDownLeft, 
  RefreshCw, 
  AlertCircle,
  Database,
  Cpu,
  UserCheck,
  Eye,
  Trash2,
  Minus,
  Plus,
  ListPlus,
  X,
  Save,
  Search
} from 'lucide-react';

import { LongScannerTab } from 'frontend/components/trading/LongScannerTab';
import { InverseEtfsTab } from 'frontend/components/trading/InverseEtfsTab';
import { ActivePositionsTab } from 'frontend/components/trading/ActivePositionsTab';
import { TradeHistoryTab } from 'frontend/components/trading/TradeHistoryTab';

const API_BASE = "http://127.0.0.1:8484/api";

interface Balance {
  cash: number;
  net_liquidation: number;
  unrealized_pnl: number;
  currency: string;
  cash_hkd?: number;
  net_liquidation_hkd?: number;
  unrealized_pnl_hkd?: number;
  currency_hkd?: string;
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
  running_us?: boolean;
  running_hk?: boolean;
  trade_mode: string;
  strategy: string;
  strategy_us?: string;
  strategy_hk?: string;
  symbols: string[];
  quantity: number;
  quantity_hk: number;
  hk_max_slots?: number;
  hk_max_price_per_slot?: number;
  hk_max_qty_per_slot?: number;
  hk_filter_price_limit?: number;
  hk_filter_price_operator?: string;
  interval: number;
  candle_period: string;
  has_client: boolean;
  // HK Risk Management
  hk_stop_loss_pct?: number;
  hk_take_profit_pct?: number;
  hk_trailing_stop_pct?: number;
  hk_max_hold_days?: number;
  hk_daily_loss_limit_hkd?: number;
  // HK ETF Settings
  hk_etf_trade_qty?: number;
  hk_etf_stop_loss_pct?: number;
  hk_etf_take_profit_pct?: number;
  hk_etf_strategy?: string;
  hk_auto_long?: boolean;
  enable_inverse_etf_hedging?: boolean;
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
  timestamp?: string;
  total?: number;
  avgBuyPrice?: number;
  realizedPnL?: number;
  pnlPct?: number;
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
  
  // HK Tickers
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
  "1818.HK": "Zhaojin Mining Industry Co., Ltd.",

  // === Hong Kong ETFs (Long, Short, and Leveraged) ===
  "2800.HK": "Tracker Fund of Hong Kong (盈富基金) - HSI Long",
  "3033.HK": "CSOP Hang Seng Tech ETF (南方恒生科技) - Tech Long",
  "2828.HK": "Hang Seng China Enterprises ETF (恒生国企) - HSCEI Long",
  "3067.HK": "iShares Hang Seng Tech ETF (iShares恒生科技)",
  "3088.HK": "ChinaAMC Hang Seng Tech ETF (华夏恒生科技)",
  "3032.HK": "Hang Seng Tech Index ETF (恒生科技ETF)",
  "2822.HK": "CSOP FTSE China A50 ETF (南方A50)",
  "3188.HK": "ChinaAMC CSI 300 Index ETF (华夏沪深300)",
  "2840.HK": "SPDR Gold Trust (SPDR黃金ETF)",
  "3160.HK": "CSOP Saudi Arabia ETF (南方沙特)",
  "3147.HK": "CSOP China IC ETF (南方半导体)",
  "3180.HK": "CSOP Hang Seng China Enterprises Index ETF",
  "3010.HK": "iShares MSCI Hong Kong ETF",
  
  // Leveraged and Inverse ETFs (HSI, HSTECH, HSCEI)
  "7200.HK": "CSOP Hang Seng Index Leveraged (ตัวคูณ 2x)",
  "7300.HK": "CSOP Hang Seng Index Inverse (ตัวคูณ -1x)",
  "7500.HK": "CSOP Hang Seng Index Inverse (ตัวคูณ -2x)",
  "7226.HK": "CSOP Hang Seng Tech Leveraged (ตัวคูณ 2x)",
  "7330.HK": "CSOP Hang Seng Tech Inverse (ตัวคูณ -1x)",
  "7552.HK": "CSOP Hang Seng Tech Inverse (ตัวคูณ -2x)",
  "7288.HK": "CSOP Hang Seng China Enterprises Leveraged (ตัวคูณ 2x)",
  "7388.HK": "CSOP Hang Seng China Enterprises Inverse (ตัวคูณ -1x)",
  "7588.HK": "CSOP Hang Seng China Enterprises Inverse (ตัวคูณ -2x)"
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
    currency: "USD",
    cash_hkd: 0.0,
    net_liquidation_hkd: 0.0,
    unrealized_pnl_hkd: 0.0,
    currency_hkd: "HKD"
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
  const [workspaceTab, setWorkspaceTab] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10); // Default to 10 rows for optimal visual balance
  const [pageEtf, setPageEtf] = useState(0);
  const [rowsPerPageEtf, setRowsPerPageEtf] = useState(10);
  const [pagePos, setPagePos] = useState(0);
  const [rowsPerPagePos, setRowsPerPagePos] = useState(10);
  const [pageHistory, setPageHistory] = useState(0);
  const [rowsPerPageHistory, setRowsPerPageHistory] = useState(10);
  const [maxPrice, setMaxPrice] = useState<string>(""); 
  const [priceOperator, setPriceOperator] = useState<"le" | "ge">("le");  
  const [searchQuery, setSearchQuery] = useState("");
  
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
        setDrawerOpen(false);
        await loadData(true);
        setIsConfigInitialized(false);
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
  const [formStrategy, setFormStrategy] = useState("rsi");
  
  // HK Settings Drawer State
  const [settingsDrawerOpen, setSettingsDrawerOpen] = useState(false);
  const [drawerSettingsTab, setDrawerSettingsTab] = useState<number>(0);
  const [formQtyHk, setFormQtyHk] = useState(100);
  const [formHkMaxSlots, setFormHkMaxSlots] = useState(1);
  const [formHkMaxPricePerSlot, setFormHkMaxPricePerSlot] = useState(999999.0);
  const [formHkMaxQtyPerSlot, setFormHkMaxQtyPerSlot] = useState(100);
  const [formHkFilterPriceLimit, setFormHkFilterPriceLimit] = useState(20.0);
  const [formHkFilterPriceOperator, setFormHkFilterPriceOperator] = useState("le");

  // HK Risk Management state
  const [formHkStopLossPct, setFormHkStopLossPct] = useState<number>(5.0);
  const [formHkTakeProfitPct, setFormHkTakeProfitPct] = useState<number>(8.0);
  const [formHkTrailingStopPct, setFormHkTrailingStopPct] = useState<number>(0.0);
  const [formHkMaxHoldDays, setFormHkMaxHoldDays] = useState<number>(0);
  const [formHkDailyLossLimitHkd, setFormHkDailyLossLimitHkd] = useState<number>(0.0);

  // HK ETF specific state
  const [formHkEtfTradeQty, setFormHkEtfTradeQty] = useState<number>(100);
  const [formHkEtfStopLossPct, setFormHkEtfStopLossPct] = useState<number>(5.0);
  const [formHkEtfTakeProfitPct, setFormHkEtfTakeProfitPct] = useState<number>(8.0);
  const [formHkEtfStrategy, setFormHkEtfStrategy] = useState<string>("trend_cash_3067");
  const [formHkAutoLong, setFormHkAutoLong] = useState<boolean>(true);
  const [formHkAutoShort, setFormHkAutoShort] = useState<boolean>(true);

  // Credentials config inputs
  const [formUsername, setFormUsername] = useState("");
  const [formPassword, setFormPassword] = useState("");
  const [formTradePin, setFormTradePin] = useState("");
  const [formAppKey, setFormAppKey] = useState("");
  const [formAppSecret, setFormAppSecret] = useState("");
  const [etfData, setEtfData] = useState<any[]>([]);

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

      const resEtf = await fetch(`${API_BASE}/etf-short-status`);
      if (resEtf.ok) {
        const dataEtf = await resEtf.json();
        setEtfData(dataEtf.filter((row: any) => row.underlying.endsWith(".HK")));
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
      setFormQtyHk(status.quantity_hk !== undefined ? status.quantity_hk : 100);
      setFormHkMaxSlots(status.hk_max_slots !== undefined ? status.hk_max_slots : 1);
      setFormHkMaxPricePerSlot(status.hk_max_price_per_slot !== undefined ? status.hk_max_price_per_slot : 999999.0);
      setFormHkMaxQtyPerSlot(status.hk_max_qty_per_slot !== undefined ? status.hk_max_qty_per_slot : 100);
      
      const filterLimit = status.hk_filter_price_limit !== undefined ? status.hk_filter_price_limit : 20.0;
      const filterOperator = status.hk_filter_price_operator !== undefined ? status.hk_filter_price_operator : "le";
      
      setFormHkFilterPriceLimit(filterLimit);
      setFormHkFilterPriceOperator(filterOperator);
      setMaxPrice(filterLimit.toString());
      setPriceOperator(filterOperator as "le" | "ge");
      // HK Risk Management
      setFormHkStopLossPct(status.hk_stop_loss_pct !== undefined ? status.hk_stop_loss_pct : 5.0);
      setFormHkTakeProfitPct(status.hk_take_profit_pct !== undefined ? status.hk_take_profit_pct : 8.0);
      setFormHkTrailingStopPct(status.hk_trailing_stop_pct !== undefined ? status.hk_trailing_stop_pct : 0.0);
      setFormHkMaxHoldDays(status.hk_max_hold_days !== undefined ? status.hk_max_hold_days : 0);
      setFormHkDailyLossLimitHkd(status.hk_daily_loss_limit_hkd !== undefined ? status.hk_daily_loss_limit_hkd : 0.0);
      
      // HK ETF Settings
      setFormHkEtfTradeQty(status.hk_etf_trade_qty !== undefined ? status.hk_etf_trade_qty : 100);
      setFormHkEtfStopLossPct(status.hk_etf_stop_loss_pct !== undefined ? status.hk_etf_stop_loss_pct : 5.0);
      setFormHkEtfTakeProfitPct(status.hk_etf_take_profit_pct !== undefined ? status.hk_etf_take_profit_pct : 8.0);
      setFormHkEtfStrategy(status.hk_etf_strategy !== undefined ? status.hk_etf_strategy : "trend_cash_3067");
      setFormHkAutoLong(status.hk_auto_long !== undefined ? status.hk_auto_long : true);
      setFormHkAutoShort(status.enable_inverse_etf_hedging !== undefined ? status.enable_inverse_etf_hedging : true);

      setFormInterval(status.interval);
      setFormPeriod(status.candle_period);
      setFormStrategy(status.strategy_hk ?? status.strategy ?? "rsi");
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
    const isRunning = status.running_hk !== undefined ? status.running_hk : status.running;
    const endpoint = isRunning ? "stop" : "start";
    try {
      const res = await fetch(`${API_BASE}/${endpoint}?market=hk`, { method: "POST" });
      const data = await res.json();
      if (!res.ok) {
        showToast(`Error: ${data.detail || "Request failed"}`, "error");
      } else {
        showToast(`บอทหุ้นฮ่องกง ${isRunning ? 'หยุดทำงาน' : 'เริ่มทำงาน'}สำเร็จ`, "success");
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
        setFormUsername("");
        setFormPassword("");
        setFormTradePin("");
        setFormAppKey("");
        setFormAppSecret("");
        await loadData();
        setIsConfigInitialized(false); // Unlock to fetch updated server values
      }
    } catch (err) {
      showToast("Failed to update config. Backend might be reinitializing.", "error");
    } finally {
      setActionLoading(false);
    }
  };

  const handleSaveHkSettings = async (e: React.FormEvent) => {
    e.preventDefault();
    setActionLoading(true);
    try {
      const res = await fetch(`${API_BASE}/config`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          trade_mode: status.trade_mode,
          symbols: status.symbols,
          quantity: status.quantity,
          quantity_hk: formQtyHk,
          hk_max_slots: formHkMaxSlots,
          hk_max_price_per_slot: formHkMaxPricePerSlot,
          hk_max_qty_per_slot: formHkMaxQtyPerSlot,
          hk_filter_price_limit: formHkFilterPriceLimit,
          hk_filter_price_operator: formHkFilterPriceOperator,
          interval: formInterval,
          candle_period: formPeriod,
          strategy: formStrategy,
          username: "",
          password: "",
          trade_pin: "",
          app_key: "",
          app_secret: "",
          // HK Risk Management
          hk_stop_loss_pct: formHkStopLossPct,
          hk_take_profit_pct: formHkTakeProfitPct,
          hk_trailing_stop_pct: formHkTrailingStopPct,
          hk_max_hold_days: formHkMaxHoldDays,
          hk_daily_loss_limit_hkd: formHkDailyLossLimitHkd,
           // HK ETF Settings
          hk_etf_trade_qty: formHkEtfTradeQty,
          hk_etf_stop_loss_pct: formHkEtfStopLossPct,
          hk_etf_take_profit_pct: formHkEtfTakeProfitPct,
          hk_etf_strategy: formHkEtfStrategy,
          hk_auto_long: formHkAutoLong,
          enable_inverse_etf_hedging: formHkAutoShort,
        })
      });

      const data = await res.json();
      if (!res.ok) {
        showToast(`บันทึกการตั้งค่าล้มเหลว: ${data.detail || "Validation failed"}`, "error");
      } else {
        showToast("บันทึกการตั้งค่าบอทฮ่องกงเรียบร้อยแล้ว!", "success");
        setSettingsDrawerOpen(false);
        await loadData(true);
        setIsConfigInitialized(false); // Reload status from server
      }
    } catch (err) {
      showToast("ไม่สามารถอัปเดตการตั้งค่าได้หลังบ้านอาจรีสตาร์ทอยู่", "error");
    } finally {
      setActionLoading(false);
    }
  };

  const handleLoadHkBudget300Defaults = () => {
    setFormQtyHk(100);
    setFormHkMaxSlots(3);
    setFormHkMaxPricePerSlot(7.8);
    setFormHkMaxQtyPerSlot(100);
    setFormInterval(60);
    setFormHkFilterPriceLimit(20.0);
    setFormHkFilterPriceOperator("le");
    setFormHkEtfTradeQty(500);
    setFormHkEtfStopLossPct(5.0);
    setFormHkEtfTakeProfitPct(8.0);
    setFormHkEtfStrategy("all");
    setFormHkAutoLong(true);
    setFormHkAutoShort(true);
    showToast("กรอกค่าตั้งแนะนำสำหรับงบไม่เกิน $300 (สะสมสูงสุด 3 Slots) เรียบร้อยแล้วครับ", "info");
  };

  const handleQuickSaveFilter = async () => {
    setActionLoading(true);
    try {
      const priceNum = parseFloat(maxPrice);
      const res = await fetch(`${API_BASE}/config`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          trade_mode: status.trade_mode,
          symbols: status.symbols,
          quantity: status.quantity,
          quantity_hk: status.quantity_hk,
          hk_max_slots: status.hk_max_slots,
          hk_max_price_per_slot: status.hk_max_price_per_slot,
          hk_max_qty_per_slot: status.hk_max_qty_per_slot,
          hk_filter_price_limit: !isNaN(priceNum) ? priceNum : 20.0,
          hk_filter_price_operator: priceOperator,
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
        showToast(`บันทึกตัวกรองล้มเหลว: ${data.detail || "Validation failed"}`, "error");
      } else {
        showToast("บันทึกตัวกรองราคา HK เริ่มต้นเป็นค่าปัจจุบันเรียบร้อยแล้ว!", "success");
        setFormHkFilterPriceLimit(!isNaN(priceNum) ? priceNum : 20.0);
        setFormHkFilterPriceOperator(priceOperator);
        await loadData(true);
        setIsConfigInitialized(false);
      }
    } catch (err) {
      showToast("ไม่สามารถบันทึกตัวกรองได้หลังบ้านอาจรีสตาร์ทอยู่", "error");
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
          hk_max_slots: status.hk_max_slots,
          hk_max_price_per_slot: status.hk_max_price_per_slot,
          hk_max_qty_per_slot: status.hk_max_qty_per_slot,
          hk_filter_price_limit: status.hk_filter_price_limit,
          hk_filter_price_operator: status.hk_filter_price_operator,
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
        await loadData(true);
        setIsConfigInitialized(false);
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
          hk_max_slots: status.hk_max_slots,
          hk_max_price_per_slot: status.hk_max_price_per_slot,
          hk_max_qty_per_slot: status.hk_max_qty_per_slot,
          hk_filter_price_limit: status.hk_filter_price_limit,
          hk_filter_price_operator: status.hk_filter_price_operator,
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
        const newHkSymbols = updatedSymbols.filter(s => s.endsWith('.HK'));
        setDrawerHkSymbols(newHkSymbols);
        await loadData(true);
        setIsConfigInitialized(false);
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

  const cashHkd = balance.cash_hkd !== undefined ? balance.cash_hkd : balance.cash * 7.8;
  const netLiqHkd = balance.net_liquidation_hkd !== undefined ? balance.net_liquidation_hkd : balance.net_liquidation * 7.8;
  const unrealizedPnHkd = balance.unrealized_pnl_hkd !== undefined ? balance.unrealized_pnl_hkd : balance.unrealized_pnl * 7.8;

  const isProfitHk = unrealizedPnHkd >= 0;
  const pnlPercentHk = (netLiqHkd - unrealizedPnHkd) > 0 
    ? (unrealizedPnHkd / (netLiqHkd - unrealizedPnHkd)) * 100 
    : 0;

  const filteredSignals = useMemo(() => {
    return signals.filter(sig => {
      const isMarketMatch = marketTab === 1 ? sig.symbol.endsWith('.HK') : !sig.symbol.endsWith('.HK');
      if (!isMarketMatch) return false;
      if (maxPrice !== "") {
        const priceNum = parseFloat(maxPrice);
        if (!isNaN(priceNum)) {
          if (priceOperator === "ge" && sig.price < priceNum) return false;
          if (priceOperator === "le" && sig.price > priceNum) return false;
        }
      }
      if (searchQuery.trim() !== "") {
        const query = searchQuery.trim().toLowerCase();
        if (!sig.symbol.toLowerCase().includes(query)) return false;
      }
      return true;
    });
  }, [signals, marketTab, maxPrice, priceOperator, searchQuery]);

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
                  ยอดเงินสดคงเหลือ ฮ่องกง
                </Typography>
                <Box sx={{ p: 1, borderRadius: '10px', bgcolor: 'rgba(59, 130, 246, 0.08)', display: 'flex' }}>
                  <Wallet size={18} color="#3b82f6" />
                </Box>
              </Box>
              <Typography variant="h4" sx={{ fontWeight: 800, fontFamily: 'var(--font-mono)', mb: 0.5, fontSize: { xs: '1.5rem', md: '1.8rem' } }}>
                {cashHkd.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })} HKD
              </Typography>
              <Typography variant="caption" color="text.secondary" sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                <Database size={10} /> เทียบเท่า: ${(cashHkd / 7.8).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })} USD
              </Typography>
            </CardContent>
          </Card>

          {/* Card 2: Net Liquidation */}
          <Card>
            <CardContent>
              <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 1.5 }}>
                <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600, letterSpacing: '0.5px' }}>
                  มูลค่าพอร์ตรวม ฮ่องกง
                </Typography>
                <Box sx={{ p: 1, borderRadius: '10px', bgcolor: 'rgba(59, 130, 246, 0.08)', display: 'flex' }}>
                  <TrendingUp size={18} color="#3b82f6" />
                </Box>
              </Box>
              <Typography variant="h4" sx={{ fontWeight: 800, fontFamily: 'var(--font-mono)', mb: 0.5, fontSize: { xs: '1.5rem', md: '1.8rem' } }}>
                {netLiqHkd.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })} HKD
              </Typography>
              <Typography variant="caption" color="text.secondary">
                เทียบเท่า: ${(netLiqHkd / 7.8).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })} USD
              </Typography>
            </CardContent>
          </Card>

          {/* Card 3: Unrealized Profit & Loss */}
          <Card>
            <CardContent>
              <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 1.5 }}>
                <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600, letterSpacing: '0.5px' }}>
                  กำไร/ขาดทุนสะสม ฮ่องกง
                </Typography>
                <Box sx={{ p: 1, borderRadius: '10px', bgcolor: isProfitHk ? 'rgba(16, 185, 129, 0.08)' : 'rgba(244, 63, 94, 0.08)', display: 'flex' }}>
                  {isProfitHk ? <TrendingUp size={18} color="#10b981" /> : <TrendingDown size={18} color="#f43f5e" />}
                </Box>
              </Box>
              <Typography 
                variant="h4" 
                color={isProfitHk ? "success.main" : "error.main"}
                sx={{ fontWeight: 800, fontFamily: 'var(--font-mono)', mb: 0.5, fontSize: { xs: '1.5rem', md: '1.8rem' } }}
              >
                {isProfitHk ? "+" : ""}{unrealizedPnHkd.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })} HKD
              </Typography>
              <Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
                <Chip 
                  label={`${isProfitHk ? "+" : ""}${pnlPercentHk.toFixed(2)}%`}
                  size="small"
                  color={isProfitHk ? "success" : "error"}
                  sx={{ height: 18, fontSize: '0.7rem', fontWeight: 700, borderRadius: '6px' }}
                />
                <Typography variant="caption" color="text.secondary">
                  เทียบเท่า: {isProfitHk ? "+" : ""}${(unrealizedPnHkd / 7.8).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })} USD
                </Typography>
              </Box>
            </CardContent>
          </Card>

          {/* Card 4: Bot status toggle control */}
          <Card sx={{ borderLeft: `2px solid ${(status.running_hk !== undefined ? status.running_hk : status.running) ? '#10b981' : '#64748b'}` }}>
            <CardContent>
              <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 1.5 }}>
                <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600, letterSpacing: '0.5px' }}>
                  สถานะการทำงานบอท ฮ่องกง
                </Typography>
                <Box sx={{ p: 1, borderRadius: '10px', bgcolor: (status.running_hk !== undefined ? status.running_hk : status.running) ? 'rgba(16, 185, 129, 0.08)' : 'rgba(100, 116, 139, 0.08)', display: 'flex' }}>
                  <Activity size={18} color={(status.running_hk !== undefined ? status.running_hk : status.running) ? "#10b981" : "#64748b"} />
                </Box>
              </Box>
              <Typography 
                variant="h4" 
                color={(status.running_hk !== undefined ? status.running_hk : status.running) ? "success.main" : "text.secondary"}
                sx={{ fontWeight: 800, mb: 0.5 }}
              >
                {(status.running_hk !== undefined ? status.running_hk : status.running) ? "RUNNING" : "STANDBY"}
              </Typography>
              
              <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mt: 0.5 }}>
                <Box sx={{ display: "flex", flexDirection: "column", gap: 0.2 }}>
                  <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 500, fontSize: '0.72rem' }}>
                    📈 Long: {(status.strategy_hk !== undefined ? status.strategy_hk : status.strategy).toUpperCase()}
                  </Typography>
                  <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 500, fontSize: '0.72rem' }}>
                    📈 ETF: {(status.hk_etf_strategy !== undefined ? status.hk_etf_strategy : "TREND_CASH_3067").toUpperCase()}
                  </Typography>
                </Box>
                
                <FormControlLabel
                  control={
                    <Switch 
                      checked={status.running_hk !== undefined ? status.running_hk : status.running} 
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
          
          {/* 3. Main Trading Workspace (Professional Tabbed Panel) */}
          <Card sx={{ background: 'linear-gradient(135deg, rgba(15, 23, 42, 0.8) 0%, rgba(30, 41, 59, 0.8) 100%)', border: '1px solid rgba(255,255,255,0.05)', borderRadius: '16px', overflow: 'hidden' }}>
            {/* Workspace Header */}
            <Box sx={{ p: 3, borderBottom: '1px solid rgba(255,255,255,0.08)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 2 }}>
              <Box sx={{ display: "flex", alignItems: "center", gap: 1.5 }}>
                <Box sx={{ p: 1, borderRadius: '10px', bgcolor: workspaceTab === 0 ? 'rgba(59, 130, 246, 0.06)' : workspaceTab === 1 ? 'rgba(244, 63, 94, 0.06)' : workspaceTab === 2 ? 'rgba(16, 185, 129, 0.06)' : 'rgba(99, 102, 241, 0.06)', display: 'flex' }}>
                  {workspaceTab === 0 ? <Eye size={20} color="#3b82f6" /> : workspaceTab === 1 ? <TrendingDown size={20} color="#f43f5e" /> : workspaceTab === 2 ? <Activity size={20} color="#10b981" /> : <History size={20} color="#6366f1" />}
                </Box>
                <Box>
                  <Typography variant="h6" sx={{ fontWeight: 800, color: '#f8fafc' }}>
                    {workspaceTab === 0 ? "สแกนเนอร์สัญญาณเทรดเรียลไทม์" : workspaceTab === 1 ? "คู่ป้องกันความเสี่ยง Inverse ETF (Short)" : workspaceTab === 2 ? "พอร์ตโฟลิโอสินทรัพย์ฮ่องกง (Positions)" : "ประวัติการเทรดฮ่องกง (HK Trade History)"}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {workspaceTab === 0 ? "วิเคราะห์ราคาปัจจุบันและประเมินทิศทางแนวโน้มตามอินดิเคเตอร์ทางเทคนิค" : workspaceTab === 1 ? "รายการจับคู่หุ้นปกติและกองทุน Inverse ETF สำหรับเก็งกำไรช่วงขาลง" : workspaceTab === 2 ? "สัญญาสมการครองชีพของหลักทรัพย์ที่ถืออยู่ในพอร์ตโฟลิโอขณะนี้" : "ประวัติธุรกรรมซื้อขายหลักทรัพย์ฮ่องกงย้อนหลังทั้งหมด"}
                  </Typography>
                </Box>
              </Box>
              
              {workspaceTab === 0 && (
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
                  <FormControl size="small" sx={{ width: 65 }}>
                    <Select
                      value={priceOperator}
                      disabled={!isConfigInitialized || actionLoading || !connected}
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
                    disabled={!isConfigInitialized || actionLoading}
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
                  <IconButton
                    color="primary"
                    size="small"
                    onClick={handleQuickSaveFilter}
                    disabled={actionLoading || !connected || !isConfigInitialized}
                    sx={{
                      mr: 1.5,
                      bgcolor: 'rgba(59, 130, 246, 0.05)',
                      border: '1px solid rgba(59, 130, 246, 0.2)',
                      borderRadius: '8px',
                      height: 34,
                      width: 34,
                      '&:hover': {
                        bgcolor: 'rgba(59, 130, 246, 0.15)',
                        borderColor: '#3b82f6',
                      }
                    }}
                    title="บันทึกตัวกรองราคานี้เป็นค่าเริ่มต้น"
                  >
                    <Save size={16} />
                  </IconButton>
                  {/* ช่องค้นหาหุ้น (Search Ticker) */}
                  <TextField
                    size="small"
                    placeholder="ค้นหาหุ้น (เช่น 0700)..."
                    value={searchQuery}
                    disabled={!isConfigInitialized || actionLoading}
                    onChange={(e) => {
                      setSearchQuery(e.target.value);
                      setPage(0);
                    }}
                    slotProps={{
                      input: {
                        startAdornment: (
                          <InputAdornment position="start">
                            <Search size={16} color="#94a3b8" />
                          </InputAdornment>
                        )
                      }
                    }}
                    sx={{ 
                      width: 240,
                      mr: 1.5,
                      '& .MuiOutlinedInput-root': {
                        borderRadius: '8px',
                        bgcolor: 'rgba(255,255,255,0.02)'
                      }
                    }}
                  />

                  <Tooltip title="จัดการรายการหุ้น (Watchlist)" arrow>
                    <span>
                      <IconButton
                        color="primary"
                        size="small"
                        disabled={actionLoading || !connected}
                        onClick={handleOpenDrawer}
                        sx={{ 
                          height: 34, 
                          width: 34,
                          borderRadius: '8px', 
                          mr: 1.5,
                          border: '1px solid rgba(59, 130, 246, 0.4)',
                          color: '#3b82f6',
                          '&:hover': {
                            borderColor: '#3b82f6',
                            bgcolor: 'rgba(59, 130, 246, 0.05)'
                          }
                        }}
                      >
                        <ListPlus size={18} />
                      </IconButton>
                    </span>
                  </Tooltip>

                  <Tooltip title="ตั้งค่าบอท (Settings)" arrow>
                    <span>
                      <IconButton
                        color="secondary"
                        size="small"
                        disabled={actionLoading || !connected}
                        onClick={() => setSettingsDrawerOpen(true)}
                        sx={{ 
                          height: 34, 
                          width: 34,
                          borderRadius: '8px', 
                          mr: 1.5,
                          border: '1px solid rgba(99, 102, 241, 0.4)',
                          color: '#a5b4fc',
                          '&:hover': {
                            borderColor: '#6366f1',
                            bgcolor: 'rgba(99, 102, 241, 0.05)'
                          }
                        }}
                      >
                        <Settings size={18} />
                      </IconButton>
                    </span>
                  </Tooltip>

                  <Tooltip title="สแกนสดทันที (Scan Now)" arrow>
                    <span>
                      <IconButton
                        color="secondary"
                        size="small"
                        disabled={isScanning || actionLoading || !connected}
                        onClick={handleManualScan}
                        sx={{ 
                          height: 34, 
                          width: 34,
                          borderRadius: '8px',
                          bgcolor: 'primary.main',
                          color: 'white',
                          '&:hover': {
                            bgcolor: 'primary.dark'
                          }
                        }}
                      >
                        {isScanning ? (
                          <RefreshCw size={18} className="spin" />
                        ) : (
                          <Play size={18} />
                        )}
                      </IconButton>
                    </span>
                  </Tooltip>
                </Box>
              )}
            </Box>

            {/* Tab Swapper */}
            <Box sx={{ borderBottom: '1px solid rgba(255,255,255,0.08)', px: 3, bgcolor: 'rgba(255,255,255,0.01)' }}>
              <Tabs 
                value={workspaceTab} 
                onChange={(e, newIdx) => setWorkspaceTab(newIdx)} 
                textColor="primary" 
                indicatorColor="primary"
              >
                <Tab label="📈 หุ้นสแกนขาขึ้น (Long Scanner)" sx={{ fontWeight: 700, py: 2, textTransform: 'none' }} />
                <Tab label="📉 ป้องกันความเสี่ยง Short (Inverse ETFs)" sx={{ fontWeight: 700, py: 2, textTransform: 'none' }} />
                <Tab label="💼 สินทรัพย์ในพอร์ต (Active Positions)" sx={{ fontWeight: 700, py: 2, textTransform: 'none' }} />
                <Tab label="📜 ประวัติการเทรด (Trade History)" sx={{ fontWeight: 700, py: 2, textTransform: 'none' }} />
              </Tabs>
            </Box>

              <CardContent sx={{ p: 0, '&:last-child': { pb: 0 } }}>
              {workspaceTab === 0 && (
                <LongScannerTab
                  market="HK"
                  filteredSignals={filteredSignals}
                  signals={signals}
                  onQuickTrade={handleQuickTrade}
                  actionLoading={actionLoading}
                  connected={connected}
                  isSignalsLoading={isSignalsLoading}
                  hasClient={status.has_client}
                  maxPrice={maxPrice}
                  priceOperator={priceOperator}
                  stockNames={STOCK_NAMES}
                />
              )}

              {workspaceTab === 1 && (
                <InverseEtfsTab
                  market="HK"
                  etfData={etfData}
                  signals={signals}
                  onQuickTrade={handleQuickTrade}
                  actionLoading={actionLoading}
                  connected={connected}
                  isSignalsLoading={isSignalsLoading}
                  hasClient={status.has_client}
                  stockNames={STOCK_NAMES}
                  hkEtfQty={formHkEtfTradeQty}
                  hkEtfStrategy={formHkEtfStrategy}
                />
              )}

              {workspaceTab === 2 && (
                <ActivePositionsTab
                  market="HK"
                  positions={positions}
                  onQuickTrade={handleQuickTrade}
                  actionLoading={actionLoading}
                  connected={connected}
                  hasClient={status.has_client}
                  stockNames={STOCK_NAMES}
                />
              )}

              {workspaceTab === 3 && (
                <TradeHistoryTab
                  market="HK"
                  trades={trades}
                  stockNames={STOCK_NAMES}
                />
              )}
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

    {/* HK Settings Drawer */}
    <Drawer
      anchor="right"
      open={settingsDrawerOpen}
      onClose={() => setSettingsDrawerOpen(false)}
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
            <Settings size={20} color="#6366f1" />
            <Typography variant="h6" sx={{ fontWeight: 800 }}>
              ตั้งค่าบอทเทรดฮ่องกง (HK Settings)
            </Typography>
          </Box>
          <IconButton onClick={() => setSettingsDrawerOpen(false)} size="small" sx={{ color: 'text.secondary' }}>
            <X size={18} />
          </IconButton>
        </Box>

        <Divider sx={{ borderColor: 'rgba(255, 255, 255, 0.06)' }} />

        {/* Settings Form */}
        <form onSubmit={handleSaveHkSettings} style={{ display: 'flex', flexDirection: 'column', gap: '20px', flex: 1, overflow: 'hidden' }}>
          <Tabs 
            value={drawerSettingsTab} 
            onChange={(e, val) => setDrawerSettingsTab(val)} 
            variant="fullWidth"
            sx={{
              borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
              mb: -1,
              '& .MuiTab-root': {
                fontWeight: 750,
                fontSize: '0.8rem',
                color: 'text.secondary',
                textTransform: 'none',
                py: 1.5,
              },
              '& .Mui-selected': {
                color: 'primary.main',
              }
            }}
          >
            <Tab label="📈 Long (ซื้อ)" />
            <Tab label="📉 Short (ETF)" />
            <Tab label="⚙️ General (ทั่วไป)" />
          </Tabs>

          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3, overflowY: 'auto', flex: 1, pr: 1 }}>
            {drawerSettingsTab === 0 && (
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                
                {/* Strategy block */}
                <Box sx={{ p: 2.5, bgcolor: 'rgba(99, 102, 241, 0.02)', borderRadius: '12px', border: '1px solid rgba(99, 102, 241, 0.12)', display: 'flex', flexDirection: 'column', gap: 2 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Typography variant="subtitle2" sx={{ fontWeight: 700, color: 'primary.main' }}>
                      📊 กลยุทธ์ส่งสัญญาณ Long
                    </Typography>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={formHkAutoLong}
                          onChange={(e) => setFormHkAutoLong(e.target.checked)}
                          color="primary"
                          size="small"
                        />
                      }
                      label={
                        <Typography variant="caption" sx={{ fontWeight: 700, color: formHkAutoLong ? 'primary.light' : 'text.secondary' }}>
                          {formHkAutoLong ? "บอททำงานอัตโนมัติ (Auto)" : "ปิดการเทรดออโต้"}
                        </Typography>
                      }
                      sx={{ m: 0 }}
                    />
                  </Box>
                  <FormControl fullWidth size="small">
                    <InputLabel>กลยุทธ์ส่งสัญญาณ (Strategy)</InputLabel>
                    <Select
                      value={formStrategy}
                      label="กลยุทธ์ส่งสัญญาณ (Strategy)"
                      onChange={(e) => {
                        const val = e.target.value;
                        setFormStrategy(val);
                        if (val === "volume_ema") {
                          setFormPeriod("m15");
                        } else if (val === "sma" || val === "hybrid") {
                          setFormPeriod("d");
                        }
                      }}
                      disabled={actionLoading}
                    >
                      <MenuItem value="rsi">RSI 14 Reversal (30/70) — ค่าแนะนำสำหรับทุน 1,000 HKD</MenuItem>
                      <MenuItem value="sma">SMA Crossover (เส้น 20/50)</MenuItem>
                      <MenuItem value="hybrid">SMA+RSI Hybrid (กลยุทธ์แม่นยำพิเศษ)</MenuItem>
                      <MenuItem value="volume_ema">Volume Spike + EMA Breakout (กลยุทธ์สำหรับทุนน้อย)</MenuItem>
                    </Select>
                  </FormControl>
                </Box>

                {/* Slots & Quantity settings */}
                <Box sx={{ p: 2.5, bgcolor: 'rgba(255, 255, 255, 0.01)', borderRadius: '12px', border: '1px solid rgba(255, 255, 255, 0.05)', display: 'flex', flexDirection: 'column', gap: 2.5 }}>
                  <Typography variant="subtitle2" sx={{ fontWeight: 700, color: 'primary.main' }}>
                    ⚙️ ขนาดการซื้อ & ขีดจำกัดสะสม Slots
                  </Typography>
                  
                  <TextField 
                    fullWidth
                    size="small"
                    label="จำนวนหุ้นซื้อเริ่มต้น ฮ่องกง (HK Shares Qty)"
                    type="number"
                    value={formQtyHk}
                    onChange={(e) => setFormQtyHk(Math.max(100, parseInt(e.target.value) || 100))}
                    slotProps={{ 
                      htmlInput: { min: 100, step: 100, style: { textAlign: 'center', fontWeight: 700 } },
                      input: {
                        startAdornment: (
                          <InputAdornment position="start">
                            <IconButton 
                              size="small" 
                              onClick={() => setFormQtyHk(prev => Math.max(100, prev - 100))}
                              disabled={actionLoading || formQtyHk <= 100}
                              sx={{ color: 'text.secondary', p: 0.5 }}
                            >
                              <Minus size={14} />
                            </IconButton>
                          </InputAdornment>
                        ),
                        endAdornment: (
                          <InputAdornment position="end">
                            <IconButton 
                              size="small" 
                              onClick={() => setFormQtyHk(prev => prev + 100)}
                              disabled={actionLoading}
                              sx={{ color: 'text.secondary', p: 0.5 }}
                            >
                              <Plus size={14} />
                            </IconButton>
                          </InputAdornment>
                        )
                      }
                    }}
                    required
                    disabled={actionLoading}
                  />

                  <TextField 
                    fullWidth
                    size="small"
                    label="จำนวนไม้ซื้อสะสมสูงสุด (HK Max Slots)"
                    type="number"
                    value={formHkMaxSlots}
                    onChange={(e) => setFormHkMaxSlots(Math.max(1, parseInt(e.target.value) || 1))}
                    slotProps={{ 
                      htmlInput: { min: 1, max: 10, style: { textAlign: 'center', fontWeight: 700 } },
                      input: {
                        startAdornment: (
                          <InputAdornment position="start">
                            <IconButton 
                              size="small" 
                              onClick={() => setFormHkMaxSlots(prev => Math.max(1, prev - 1))}
                              disabled={actionLoading || formHkMaxSlots <= 1}
                              sx={{ color: 'text.secondary', p: 0.5 }}
                            >
                              <Minus size={14} />
                            </IconButton>
                          </InputAdornment>
                        ),
                        endAdornment: (
                          <InputAdornment position="end">
                            <IconButton 
                              size="small" 
                              onClick={() => setFormHkMaxSlots(prev => prev + 1)}
                              disabled={actionLoading}
                              sx={{ color: 'text.secondary', p: 0.5 }}
                            >
                              <Plus size={14} />
                            </IconButton>
                          </InputAdornment>
                        )
                      }
                    }}
                    required
                    disabled={actionLoading}
                  />

                  <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 1.5 }}>
                    <TextField 
                      fullWidth
                      size="small"
                      label="ราคาหุ้นสูงสุดต่อไม้ (Max Price/Slot)"
                      type="number"
                      value={formHkMaxPricePerSlot}
                      onChange={(e) => setFormHkMaxPricePerSlot(Math.max(0, parseFloat(e.target.value) || 0))}
                      slotProps={{ 
                        htmlInput: { min: 0, step: 0.5, style: { textAlign: 'center', fontWeight: 700 } },
                        input: {
                          startAdornment: (
                            <InputAdornment position="start">
                              <IconButton 
                                size="small" 
                                onClick={() => setFormHkMaxPricePerSlot(prev => Math.max(0.0, Math.round((prev - 1) * 10) / 10))}
                                disabled={actionLoading || formHkMaxPricePerSlot <= 0}
                                sx={{ color: 'text.secondary', p: 0.5 }}
                              >
                                <Minus size={14} />
                              </IconButton>
                            </InputAdornment>
                          ),
                          endAdornment: (
                            <InputAdornment position="end">
                              <IconButton 
                                size="small" 
                                onClick={() => setFormHkMaxPricePerSlot(prev => Math.round((prev + 1) * 10) / 10)}
                                disabled={actionLoading}
                                sx={{ color: 'text.secondary', p: 0.5 }}
                              >
                                <Plus size={14} />
                              </IconButton>
                            </InputAdornment>
                          )
                        }
                      }}
                      required
                      disabled={actionLoading}
                    />

                    <TextField 
                      fullWidth
                      size="small"
                      label="จำนวนหุ้นสูงสุดต่อไม้ (Max Qty/Slot)"
                      type="number"
                      value={formHkMaxQtyPerSlot}
                      onChange={(e) => setFormHkMaxQtyPerSlot(Math.max(100, parseInt(e.target.value) || 100))}
                      slotProps={{ 
                        htmlInput: { min: 100, step: 100, style: { textAlign: 'center', fontWeight: 700 } },
                        input: {
                          startAdornment: (
                            <InputAdornment position="start">
                              <IconButton 
                                size="small" 
                                onClick={() => setFormHkMaxQtyPerSlot(prev => Math.max(100, prev - 100))}
                                disabled={actionLoading || formHkMaxQtyPerSlot <= 100}
                                sx={{ color: 'text.secondary', p: 0.5 }}
                              >
                                <Minus size={14} />
                              </IconButton>
                            </InputAdornment>
                          ),
                          endAdornment: (
                            <InputAdornment position="end">
                              <IconButton 
                                size="small" 
                                onClick={() => setFormHkMaxQtyPerSlot(prev => prev + 100)}
                                disabled={actionLoading}
                                sx={{ color: 'text.secondary', p: 0.5 }}
                              >
                                <Plus size={14} />
                              </IconButton>
                            </InputAdornment>
                          )
                        }
                      }}
                      required
                      disabled={actionLoading}
                    />
                  </Box>
                </Box>

                {/* Price filter settings */}
                <Box sx={{ p: 2.5, bgcolor: 'rgba(255, 255, 255, 0.01)', borderRadius: '12px', border: '1px solid rgba(255, 255, 255, 0.05)', display: 'flex', flexDirection: 'column', gap: 2.5 }}>
                  <Typography variant="subtitle2" sx={{ fontWeight: 700, color: 'primary.main' }}>
                    🔍 ตัวกรองราคาซื้อหุ้นหลัก (HK Price Filter)
                  </Typography>
                  <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 1.5 }}>
                    <FormControl fullWidth size="small">
                      <InputLabel>เงื่อนไข (Operator)</InputLabel>
                      <Select
                        value={formHkFilterPriceOperator}
                        label="เงื่อนไข (Operator)"
                        onChange={(e) => setFormHkFilterPriceOperator(e.target.value)}
                        disabled={actionLoading}
                      >
                        <MenuItem value="le">น้อยกว่าหรือเท่ากับ (&le;)</MenuItem>
                        <MenuItem value="ge">มากกว่าหรือเท่ากับ (&ge;)</MenuItem>
                      </Select>
                    </FormControl>
                    <TextField 
                      fullWidth
                      size="small"
                      label="เป้าหมายราคา (HKD)"
                      type="number"
                      value={formHkFilterPriceLimit}
                      onChange={(e) => setFormHkFilterPriceLimit(Math.max(0, parseFloat(e.target.value) || 0))}
                      slotProps={{ 
                        htmlInput: { min: 0, step: 1, style: { textAlign: 'center', fontWeight: 700 } },
                        input: {
                          startAdornment: (
                            <InputAdornment position="start">
                              <IconButton 
                                size="small" 
                                onClick={() => setFormHkFilterPriceLimit(prev => Math.max(0, prev - 1))}
                                disabled={actionLoading || formHkFilterPriceLimit <= 0}
                                sx={{ color: 'text.secondary', p: 0.5 }}
                              >
                                <Minus size={14} />
                              </IconButton>
                            </InputAdornment>
                          ),
                          endAdornment: (
                            <InputAdornment position="end">
                              <IconButton 
                                size="small" 
                                onClick={() => setFormHkFilterPriceLimit(prev => prev + 1)}
                                disabled={actionLoading}
                                sx={{ color: 'text.secondary', p: 0.5 }}
                              >
                                <Plus size={14} />
                              </IconButton>
                            </InputAdornment>
                          )
                        }
                      }}
                      required
                      disabled={actionLoading}
                    />
                  </Box>
                </Box>

                {/* Risk Management Long settings */}
                <Box sx={{ p: 2.5, bgcolor: 'rgba(234, 57, 67, 0.02)', borderRadius: '12px', border: '1px solid rgba(234, 57, 67, 0.12)', display: 'flex', flexDirection: 'column', gap: 2.5 }}>
                  <Typography variant="subtitle2" sx={{ fontWeight: 700, color: 'error.main' }}>
                    🛑 ระบบตัดขาดทุน & ทำกำไร Long (Risk Controls)
                  </Typography>

                  <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 1.5 }}>
                    <TextField
                      fullWidth size="small"
                      label="🛑 Stop Loss (%)"
                      type="number"
                      value={formHkStopLossPct}
                      onChange={(e) => setFormHkStopLossPct(Math.max(0, parseFloat(e.target.value) || 0))}
                      disabled={actionLoading}
                      helperText={formHkStopLossPct > 0 ? `ร่วง ${formHkStopLossPct}%` : "ปิด"}
                      slotProps={{
                        htmlInput: { min: 0, step: 0.5, style: { textAlign: 'center', fontWeight: 700 } },
                        input: {
                          startAdornment: (
                            <InputAdornment position="start">
                              <IconButton 
                                size="small" 
                                onClick={() => setFormHkStopLossPct(prev => Math.max(0, prev - 0.5))}
                                disabled={actionLoading || formHkStopLossPct <= 0}
                                sx={{ color: 'text.secondary', p: 0.5 }}
                              >
                                <Minus size={14} />
                              </IconButton>
                            </InputAdornment>
                          ),
                          endAdornment: (
                            <InputAdornment position="end">
                              <IconButton 
                                size="small" 
                                onClick={() => setFormHkStopLossPct(prev => prev + 0.5)}
                                disabled={actionLoading}
                                sx={{ color: 'text.secondary', p: 0.5 }}
                              >
                                <Plus size={14} />
                              </IconButton>
                            </InputAdornment>
                          )
                        }
                      }}
                    />
                    <TextField
                      fullWidth size="small"
                      label="✅ Take Profit (%)"
                      type="number"
                      value={formHkTakeProfitPct}
                      onChange={(e) => setFormHkTakeProfitPct(Math.max(0, parseFloat(e.target.value) || 0))}
                      disabled={actionLoading}
                      helperText={formHkTakeProfitPct > 0 ? `ขึ้น ${formHkTakeProfitPct}%` : "ปิด"}
                      slotProps={{
                        htmlInput: { min: 0, step: 0.5, style: { textAlign: 'center', fontWeight: 700 } },
                        input: {
                          startAdornment: (
                            <InputAdornment position="start">
                              <IconButton 
                                size="small" 
                                onClick={() => setFormHkTakeProfitPct(prev => Math.max(0, prev - 0.5))}
                                disabled={actionLoading || formHkTakeProfitPct <= 0}
                                sx={{ color: 'text.secondary', p: 0.5 }}
                              >
                                <Minus size={14} />
                              </IconButton>
                            </InputAdornment>
                          ),
                          endAdornment: (
                            <InputAdornment position="end">
                              <IconButton 
                                size="small" 
                                onClick={() => setFormHkTakeProfitPct(prev => prev + 0.5)}
                                disabled={actionLoading}
                                sx={{ color: 'text.secondary', p: 0.5 }}
                              >
                                <Plus size={14} />
                              </IconButton>
                            </InputAdornment>
                          )
                        }
                      }}
                    />
                  </Box>

                  <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 1.5 }}>
                    <TextField
                      fullWidth size="small"
                      label="📉 Trailing Stop (%)"
                      type="number"
                      value={formHkTrailingStopPct}
                      onChange={(e) => setFormHkTrailingStopPct(Math.max(0, parseFloat(e.target.value) || 0))}
                      disabled={actionLoading}
                      helperText={formHkTrailingStopPct > 0 ? `ล็อคกำไรเมื่อย่อ ${formHkTrailingStopPct}%` : "ปิด"}
                      slotProps={{
                        htmlInput: { min: 0, step: 0.5, style: { textAlign: 'center', fontWeight: 700 } },
                        input: {
                          startAdornment: (
                            <InputAdornment position="start">
                              <IconButton 
                                size="small" 
                                onClick={() => setFormHkTrailingStopPct(prev => Math.max(0, prev - 0.5))}
                                disabled={actionLoading || formHkTrailingStopPct <= 0}
                                sx={{ color: 'text.secondary', p: 0.5 }}
                              >
                                <Minus size={14} />
                              </IconButton>
                            </InputAdornment>
                          ),
                          endAdornment: (
                            <InputAdornment position="end">
                              <IconButton 
                                size="small" 
                                onClick={() => setFormHkTrailingStopPct(prev => prev + 0.5)}
                                disabled={actionLoading}
                                sx={{ color: 'text.secondary', p: 0.5 }}
                              >
                                <Plus size={14} />
                              </IconButton>
                            </InputAdornment>
                          )
                        }
                      }}
                    />
                    <TextField
                      fullWidth size="small"
                      label="📅 Max Hold (Days)"
                      type="number"
                      value={formHkMaxHoldDays}
                      onChange={(e) => setFormHkMaxHoldDays(Math.max(0, parseInt(e.target.value) || 0))}
                      disabled={actionLoading}
                      helperText={formHkMaxHoldDays > 0 ? `เคลียร์พอร์ตเมื่อครบ ${formHkMaxHoldDays} วัน` : "ปิด"}
                      slotProps={{
                        htmlInput: { min: 0, step: 1, style: { textAlign: 'center', fontWeight: 700 } },
                        input: {
                          startAdornment: (
                            <InputAdornment position="start">
                              <IconButton 
                                size="small" 
                                onClick={() => setFormHkMaxHoldDays(prev => Math.max(0, prev - 1))}
                                disabled={actionLoading || formHkMaxHoldDays <= 0}
                                sx={{ color: 'text.secondary', p: 0.5 }}
                              >
                                <Minus size={14} />
                              </IconButton>
                            </InputAdornment>
                          ),
                          endAdornment: (
                            <InputAdornment position="end">
                              <IconButton 
                                size="small" 
                                onClick={() => setFormHkMaxHoldDays(prev => prev + 1)}
                                disabled={actionLoading}
                                sx={{ color: 'text.secondary', p: 0.5 }}
                              >
                                <Plus size={14} />
                              </IconButton>
                            </InputAdornment>
                          )
                        }
                      }}
                    />
                  </Box>
                </Box>
              </Box>
            )}

            {drawerSettingsTab === 1 && (
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                {/* HK ETF Settings Section */}
                <Box sx={{ p: 2.5, bgcolor: 'rgba(99, 102, 241, 0.03)', borderRadius: '12px', border: '1px solid rgba(99, 102, 241, 0.15)', display: 'flex', flexDirection: 'column', gap: 2.5 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Box sx={{ p: 0.8, borderRadius: '8px', bgcolor: 'rgba(99, 102, 241, 0.1)', display: 'flex' }}>
                        <span style={{ fontSize: 14 }}>📈</span>
                      </Box>
                      <Box>
                        <Typography variant="subtitle2" sx={{ fontWeight: 800, color: '#a5b4fc', lineHeight: 1.2 }}>
                          ตั้งค่ากลยุทธ์ ETF (HK ETF Settings)
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          เลือกกลยุทธ์ Long ETF หรือ Inverse ETF และกำหนดการควบคุมความเสี่ยง
                        </Typography>
                      </Box>
                    </Box>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={formHkAutoShort}
                          onChange={(e) => setFormHkAutoShort(e.target.checked)}
                          color="primary"
                          size="small"
                        />
                      }
                      label={
                        <Typography variant="caption" sx={{ fontWeight: 700, color: formHkAutoShort ? 'primary.light' : 'text.secondary' }}>
                          {formHkAutoShort ? "ETF Auto เปิดอยู่" : "ETF Auto ปิดอยู่"}
                        </Typography>
                      }
                      sx={{ m: 0, ml: 1 }}
                    />
                  </Box>

                  <FormControl fullWidth size="small">
                    <InputLabel>กลยุทธ์อ้างอิงสำหรับ ETF (ETF Strategy)</InputLabel>
                    <Select
                      value={formHkEtfStrategy}
                      label="กลยุทธ์อ้างอิงสำหรับ ETF (ETF Strategy)"
                      onChange={(e) => setFormHkEtfStrategy(e.target.value)}
                      disabled={actionLoading}
                    >
                      <MenuItem value="trend_cash_3067">3067 Trend + Cash (SMA20/50 + Momentum20) — แนะนำ</MenuItem>
                      <MenuItem value="all">Composite Score (รวมทุกอินดิเคเตอร์)</MenuItem>
                      <MenuItem value="volume_ema">Volume Spike + EMA Breakout</MenuItem>
                      <MenuItem value="sma">SMA Crossover</MenuItem>
                      <MenuItem value="rsi">RSI Reversal</MenuItem>
                      <MenuItem value="hybrid">SMA+RSI Hybrid</MenuItem>
                    </Select>
                  </FormControl>

                  <TextField 
                    fullWidth
                    size="small"
                    label="จำนวนหน่วยซื้อ ETF เริ่มต้น (HK ETF Qty)"
                    type="number"
                    value={formHkEtfTradeQty}
                    onChange={(e) => setFormHkEtfTradeQty(Math.max(100, parseInt(e.target.value) || 100))}
                    slotProps={{ 
                      htmlInput: { min: 100, step: 100, style: { textAlign: 'center', fontWeight: 700 } },
                      input: {
                        startAdornment: (
                          <InputAdornment position="start">
                            <IconButton 
                              size="small" 
                              onClick={() => setFormHkEtfTradeQty(prev => Math.max(100, prev - 100))}
                              disabled={actionLoading || formHkEtfTradeQty <= 100}
                              sx={{ color: 'text.secondary', p: 0.5 }}
                            >
                              <Minus size={14} />
                            </IconButton>
                          </InputAdornment>
                        ),
                        endAdornment: (
                          <InputAdornment position="end">
                            <IconButton 
                              size="small" 
                              onClick={() => setFormHkEtfTradeQty(prev => prev + 100)}
                              disabled={actionLoading}
                              sx={{ color: 'text.secondary', p: 0.5 }}
                            >
                              <Plus size={14} />
                            </IconButton>
                          </InputAdornment>
                        )
                      }
                    }}
                    required
                    disabled={actionLoading}
                  />

                  <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 1.5 }}>
                    <TextField
                      fullWidth size="small"
                      label="🛑 ETF Stop Loss (%)"
                      type="number"
                      value={formHkEtfStopLossPct}
                      onChange={(e) => setFormHkEtfStopLossPct(Math.max(0, parseFloat(e.target.value) || 0))}
                      disabled={actionLoading}
                      helperText={formHkEtfStopLossPct > 0 ? `ร่วง ${formHkEtfStopLossPct}%` : "ปิด"}
                      slotProps={{
                        htmlInput: { min: 0, step: 0.5, style: { textAlign: 'center', fontWeight: 700 } },
                        input: {
                          startAdornment: (
                            <InputAdornment position="start">
                              <IconButton 
                                size="small" 
                                onClick={() => setFormHkEtfStopLossPct(prev => Math.max(0, prev - 0.5))}
                                disabled={actionLoading || formHkEtfStopLossPct <= 0}
                                sx={{ color: 'text.secondary', p: 0.5 }}
                              >
                                <Minus size={14} />
                              </IconButton>
                            </InputAdornment>
                          ),
                          endAdornment: (
                            <InputAdornment position="end">
                              <IconButton 
                                size="small" 
                                onClick={() => setFormHkEtfStopLossPct(prev => prev + 0.5)}
                                disabled={actionLoading}
                                sx={{ color: 'text.secondary', p: 0.5 }}
                              >
                                <Plus size={14} />
                              </IconButton>
                            </InputAdornment>
                          )
                        }
                      }}
                    />
                    <TextField
                      fullWidth size="small"
                      label="✅ ETF Take Profit (%)"
                      type="number"
                      value={formHkEtfTakeProfitPct}
                      onChange={(e) => setFormHkEtfTakeProfitPct(Math.max(0, parseFloat(e.target.value) || 0))}
                      disabled={actionLoading}
                      helperText={formHkEtfTakeProfitPct > 0 ? `ขึ้น ${formHkEtfTakeProfitPct}%` : "ปิด"}
                      slotProps={{
                        htmlInput: { min: 0, step: 0.5, style: { textAlign: 'center', fontWeight: 700 } },
                        input: {
                          startAdornment: (
                            <InputAdornment position="start">
                              <IconButton 
                                size="small" 
                                onClick={() => setFormHkEtfTakeProfitPct(prev => Math.max(0, prev - 0.5))}
                                disabled={actionLoading || formHkEtfTakeProfitPct <= 0}
                                sx={{ color: 'text.secondary', p: 0.5 }}
                              >
                                <Minus size={14} />
                              </IconButton>
                            </InputAdornment>
                          ),
                          endAdornment: (
                            <InputAdornment position="end">
                              <IconButton 
                                size="small" 
                                onClick={() => setFormHkEtfTakeProfitPct(prev => prev + 0.5)}
                                disabled={actionLoading}
                                sx={{ color: 'text.secondary', p: 0.5 }}
                              >
                                <Plus size={14} />
                              </IconButton>
                            </InputAdornment>
                          )
                        }
                      }}
                    />
                  </Box>
                </Box>
              </Box>
            )}

            {drawerSettingsTab === 2 && (
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                
                {/* ⚡ แนะนำตามงบประมาณ */}
                <Box sx={{ p: 2, bgcolor: 'rgba(99, 102, 241, 0.02)', borderRadius: '12px', border: '1px solid rgba(99, 102, 241, 0.1)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Box sx={{ mr: 1 }}>
                    <Typography variant="subtitle2" sx={{ fontWeight: 700, color: 'text.primary' }}>
                      ⚡ แนะนำตามงบประมาณ
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      โหลดค่าตัวแปรเบื้องต้นสำหรับงบไม่เกิน $300
                    </Typography>
                  </Box>
                  <Button
                    size="small"
                    variant="outlined"
                    color="secondary"
                    onClick={handleLoadHkBudget300Defaults}
                    sx={{ 
                      fontSize: '0.72rem', 
                      py: 0.6, 
                      px: 1.5, 
                      borderRadius: '6px',
                      borderColor: 'rgba(99, 102, 241, 0.4)',
                      color: '#a5b4fc',
                      textTransform: 'none',
                      flexShrink: 0,
                      '&:hover': {
                        borderColor: '#6366f1',
                        bgcolor: 'rgba(99, 102, 241, 0.05)'
                      }
                    }}
                  >
                    โหลดค่าอัตโนมัติ
                  </Button>
                </Box>

                {/* System settings block */}
                <Box sx={{ p: 2.5, bgcolor: 'rgba(255, 255, 255, 0.01)', borderRadius: '12px', border: '1px solid rgba(255, 255, 255, 0.05)', display: 'flex', flexDirection: 'column', gap: 2.5 }}>
                  <Typography variant="subtitle2" sx={{ fontWeight: 700, color: 'primary.main' }}>
                    ⚙️ การทำงานของระบบบอท
                  </Typography>

                  <FormControl fullWidth size="small">
                    <InputLabel>ขนาดเวลาแท่งเทียน (Candle Period)</InputLabel>
                    <Select
                      value={formPeriod}
                      label="ขนาดเวลาแท่งเทียน (Candle Period)"
                      onChange={(e) => setFormPeriod(e.target.value)}
                      disabled={actionLoading}
                    >
                      <MenuItem value="m1">1 Minute</MenuItem>
                      <MenuItem value="m5">5 Minutes</MenuItem>
                      <MenuItem value="m15">15 Minutes (แนะนำสำหรับ Vol+EMA)</MenuItem>
                      <MenuItem value="m30">30 Minutes</MenuItem>
                      <MenuItem value="h1">1 Hour</MenuItem>
                      <MenuItem value="d">1 Day (แนะนำสำหรับ SMA/Hybrid)</MenuItem>
                    </Select>
                  </FormControl>

                  <TextField 
                    fullWidth
                    size="small"
                    label="ความถี่ตรวจสอบและสแกนราคา (วินาที)"
                    type="number"
                    value={formInterval}
                    onChange={(e) => setFormInterval(Math.max(30, parseInt(e.target.value) || 60))}
                    slotProps={{ 
                      htmlInput: { min: 30, step: 10, style: { textAlign: 'center', fontWeight: 700 } },
                      input: {
                        startAdornment: (
                          <InputAdornment position="start">
                            <IconButton 
                              size="small" 
                              onClick={() => setFormInterval(prev => Math.max(30, prev - 10))}
                              disabled={actionLoading || formInterval <= 30}
                              sx={{ color: 'text.secondary', p: 0.5 }}
                            >
                              <Minus size={14} />
                            </IconButton>
                          </InputAdornment>
                        ),
                        endAdornment: (
                          <InputAdornment position="end">
                            <IconButton 
                              size="small" 
                              onClick={() => setFormInterval(prev => prev + 10)}
                              disabled={actionLoading}
                              sx={{ color: 'text.secondary', p: 0.5 }}
                            >
                              <Plus size={14} />
                            </IconButton>
                          </InputAdornment>
                        )
                      }
                    }}
                    required
                    disabled={actionLoading}
                  />

                  <TextField
                    fullWidth size="small"
                    label="⛔ Daily Loss Limit (HKD)"
                    type="number"
                    value={formHkDailyLossLimitHkd}
                    onChange={(e) => setFormHkDailyLossLimitHkd(Math.max(0, parseFloat(e.target.value) || 0))}
                    disabled={actionLoading}
                    helperText={formHkDailyLossLimitHkd > 0 ? `หยุด bot ถ้าขาดทุน > ${formHkDailyLossLimitHkd.toLocaleString()} HKD/วัน` : "ปิด"}
                    slotProps={{
                      htmlInput: { min: 0, step: 100, style: { textAlign: 'center', fontWeight: 700 } },
                      input: {
                        startAdornment: (
                          <InputAdornment position="start">
                            <IconButton 
                              size="small" 
                              onClick={() => setFormHkDailyLossLimitHkd(prev => Math.max(0, prev - 100))}
                              disabled={actionLoading || formHkDailyLossLimitHkd <= 0}
                              sx={{ color: 'text.secondary', p: 0.5 }}
                            >
                              <Minus size={14} />
                            </IconButton>
                          </InputAdornment>
                        ),
                        endAdornment: (
                          <InputAdornment position="end">
                            <IconButton 
                              size="small" 
                              onClick={() => setFormHkDailyLossLimitHkd(prev => prev + 100)}
                              disabled={actionLoading}
                              sx={{ color: 'text.secondary', p: 0.5 }}
                            >
                              <Plus size={14} />
                            </IconButton>
                          </InputAdornment>
                        )
                      }
                    }}
                  />
                </Box>
              </Box>
            )}
          </Box>
          {/* Drawer Bottom Actions */}
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5, mt: 'auto', pt: 2, borderTop: '1px solid rgba(255, 255, 255, 0.06)' }}>
            <Button
              variant="contained"
              color="primary"
              type="submit"
              fullWidth
              disabled={actionLoading}
              sx={{ py: 1.2, fontWeight: 700, borderRadius: '8px' }}
            >
              {actionLoading ? <RefreshCw className="spin" size={18} /> : "บันทึก & รีโหลดบอท (Save & Hot-Reload)"}
            </Button>
            <Typography variant="caption" color="text.secondary" align="center">
              * การกดบันทึกจะเขียนทับการตั้งค่าบอทและรีสตาร์ทบอทเพื่อรับค่าใหม่ทันที
            </Typography>
          </Box>
        </form>
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
