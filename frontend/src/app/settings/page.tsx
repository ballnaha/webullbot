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
  TextField, 
  Select, 
  MenuItem, 
  FormControl, 
  InputLabel, 
  Alert, 
  AlertTitle,
  InputAdornment,
  IconButton
} from '@mui/material';

import Header from 'frontend/components/Header';
import { useToast } from 'frontend/components/ToastProvider';

import { 
  Settings, 
  UserCheck, 
  RefreshCw, 
  AlertCircle,
  Minus,
  Plus
} from 'lucide-react';

const API_BASE = "http://127.0.0.1:8484/api";

interface BotStatus {
  running: boolean;
  trade_mode: string;
  strategy: string;
  symbols: string[];
  quantity: number;
  quantity_hk: number;
  hk_max_slots?: number;
  hk_max_price_per_slot?: number;
  hk_max_qty_per_slot?: number;
  hk_filter_price_limit?: number;
  hk_filter_price_operator?: string;
  strategy_us?: string;
  strategy_hk?: string;
  interval: number;
  candle_period: string;
  simulated_initial_cash?: number;
  simulated_initial_cash_hkd?: number;
  has_client: boolean;
  init_status?: string;
  init_error?: string;
  // HK Risk Management
  hk_stop_loss_pct?: number;
  hk_take_profit_pct?: number;
  hk_trailing_stop_pct?: number;
  hk_max_hold_days?: number;
  hk_daily_loss_limit_hkd?: number;
}

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
  },
});

export default function SettingsPage() {
  const { showToast } = useToast();
  const [mounted, setMounted] = useState(false);
  const [connected, setConnected] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState(false);

  // Status state
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

  // Config form state
  const [formMode, setFormMode] = useState("LOCAL_PAPER");
  const [formSimulatedInitialCash, setFormSimulatedInitialCash] = useState<number>(300);
  const [formSimulatedInitialCashHkd, setFormSimulatedInitialCashHkd] = useState<number>(2340);
  const [isConfigInitialized, setIsConfigInitialized] = useState(false);

  // Credentials config inputs
  const [formUsername, setFormUsername] = useState("");
  const [formPassword, setFormPassword] = useState("");
  const [formTradePin, setFormTradePin] = useState("");
  const [formAppKey, setFormAppKey] = useState("");
  const [formAppSecret, setFormAppSecret] = useState("");

  const loadData = useCallback(async () => {
    try {
      const resStatus = await fetch(`${API_BASE}/status`);
      if (!resStatus.ok) throw new Error("Backend response error");
      const dataStatus = await resStatus.json();
      setStatus(dataStatus);
      setConnected(true);
      setApiError(null);
    } catch (err: any) {
      setConnected(false);
      setApiError(err.message || "Cannot connect to Python API server. Ensure server.py is running on port 8484.");
    }
  }, []);

  useEffect(() => {
    setMounted(true);
    loadData();
    const intervalId = setInterval(loadData, 3000);
    return () => clearInterval(intervalId);
  }, [loadData]);

  useEffect(() => {
    if (!isConfigInitialized && status.trade_mode !== "") {
      setFormMode(status.trade_mode);
      setFormSimulatedInitialCash(status.simulated_initial_cash !== undefined ? status.simulated_initial_cash : 300);
      setFormSimulatedInitialCashHkd(status.simulated_initial_cash_hkd !== undefined ? status.simulated_initial_cash_hkd : 2340);
      setIsConfigInitialized(true);
    }
  }, [status, isConfigInitialized]);

  const handleSaveConfig = async (e: React.FormEvent) => {
    e.preventDefault();
    setActionLoading(true);

    try {
      const res = await fetch(`${API_BASE}/config`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          trade_mode: formMode,
          symbols: status.symbols,
          quantity: status.quantity !== undefined ? status.quantity : 1,
          interval: status.interval !== undefined ? status.interval : 60,
          candle_period: status.candle_period !== undefined ? status.candle_period : "m5",
          strategy_us: status.strategy_us !== undefined ? status.strategy_us : "sma",
          strategy_hk: status.strategy_hk !== undefined ? status.strategy_hk : "sma",
          hk_filter_price_limit: status.hk_filter_price_limit !== undefined ? status.hk_filter_price_limit : 20.0,
          hk_filter_price_operator: status.hk_filter_price_operator !== undefined ? status.hk_filter_price_operator : "le",
          simulated_initial_cash: formSimulatedInitialCash,
          simulated_initial_cash_hkd: formSimulatedInitialCashHkd,
          hk_stop_loss_pct: status.hk_stop_loss_pct !== undefined ? status.hk_stop_loss_pct : 5.0,
          hk_take_profit_pct: status.hk_take_profit_pct !== undefined ? status.hk_take_profit_pct : 8.0,
          hk_trailing_stop_pct: status.hk_trailing_stop_pct !== undefined ? status.hk_trailing_stop_pct : 0.0,
          hk_max_hold_days: status.hk_max_hold_days !== undefined ? status.hk_max_hold_days : 0,
          hk_daily_loss_limit_hkd: status.hk_daily_loss_limit_hkd !== undefined ? status.hk_daily_loss_limit_hkd : 0.0,
          username: formUsername,
          password: formPassword,
          trade_pin: formTradePin,
          app_key: formAppKey,
          app_secret: formAppSecret,
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

        // Fetch fresh status and directly update form values
        try {
          const freshRes = await fetch(`${API_BASE}/status`);
          if (freshRes.ok) {
            const freshStatus = await freshRes.json();
            setStatus(freshStatus);
            // Directly sync form from fresh server values
            setFormMode(freshStatus.trade_mode);
            setFormSimulatedInitialCash(freshStatus.simulated_initial_cash !== undefined ? freshStatus.simulated_initial_cash : 300);
            setFormSimulatedInitialCashHkd(freshStatus.simulated_initial_cash_hkd !== undefined ? freshStatus.simulated_initial_cash_hkd : 2340);
          }
        } catch (_) { /* silent */ }
        setIsConfigInitialized(true);
      }
    } catch (err) {
      showToast("Failed to update config. Backend might be reinitializing.", "error");
    } finally {
      setActionLoading(false);
    }
  };

  return (
    <>

        {/* Settings Form Container */}
        <Card sx={{ background: 'linear-gradient(135deg, rgba(15, 23, 42, 0.8) 0%, rgba(30, 41, 59, 0.8) 100%)' }}>
          <CardContent sx={{ p: 4 }}>
            <Box sx={{ display: "flex", alignItems: "center", gap: 2, mb: 4 }}>
              <Box sx={{ p: 1.5, borderRadius: '12px', bgcolor: 'rgba(0, 242, 254, 0.06)', display: 'flex' }}>
                <Settings size={24} color="#3b82f6" />
              </Box>
              <Box>
                <Typography variant="h5" sx={{ fontWeight: 800 }}>
                  ตั้งค่าระบบเทรดและกลยุทธ์บอท (Bot Configuration)
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  ปรับปรุงโหมดการซื้อขาย บัญชีการเชื่อมต่อบอท และสัญลักษณ์ Watchlist ที่ต้องการสแกน
                </Typography>
              </Box>
            </Box>

            <form onSubmit={handleSaveConfig}>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3.5 }}>
                
                {status.init_status === "initializing" && (
                  <Alert severity="info" sx={{ borderRadius: '12px', border: '1px solid rgba(59, 130, 246, 0.15)', bgcolor: 'rgba(59, 130, 246, 0.05)' }}>
                    <AlertTitle sx={{ fontWeight: 700 }}>กำลังเชื่อมต่อระบบและตั้งค่าบอท (Initializing...)</AlertTitle>
                    ระบบหลังบ้านกำลังดำเนินการล็อกอินเข้าสู่ระบบและโหลดค่าบัญชีของคุณในพื้นหลัง กรุณารอสักครู่...
                  </Alert>
                )}

                {status.init_status === "failed" && (
                  <Alert severity="error" sx={{ borderRadius: '12px', border: '1px solid rgba(234, 57, 67, 0.15)', bgcolor: 'rgba(234, 57, 67, 0.05)' }}>
                    <AlertTitle sx={{ fontWeight: 700 }}>การเชื่อมต่อล้มเหลว (Initialization Failed)</AlertTitle>
                    {status.init_error || "เกิดข้อผิดพลาดในการโหลดค่าบัญชีเทรดของคุณ กรุณาตรวจสอบข้อมูลการเชื่อมต่อและกดบันทึกใหม่อีกครั้ง"}
                  </Alert>
                )}

                {/* 1. Trade Mode */}
                <FormControl fullWidth size="small">
                  <InputLabel>โหมดการเทรด (Trading Mode)</InputLabel>
                  <Select
                    value={formMode}
                    label="โหมดการเทรด (Trading Mode)"
                    onChange={(e) => setFormMode(e.target.value)}
                    disabled={actionLoading}
                    sx={{ borderRadius: '12px' }}
                  >
                    <MenuItem value="LOCAL_PAPER">LOCAL_PAPER (จำลองในระบบจำลอง)</MenuItem>
                    <MenuItem value="WEBULL_PAPER">WEBULL_PAPER (จำลองตลาด Webull)</MenuItem>
                    <MenuItem value="WEBULL_LIVE">WEBULL_LIVE (บัญชีจริง Webull)</MenuItem>
                    <MenuItem value="WEBULL_OFFICIAL">WEBULL_OFFICIAL (OpenAPI ทางการ)</MenuItem>
                  </Select>
                </FormControl>

                {/* 2. Credentials details */}
                {formMode === "WEBULL_OFFICIAL" ? (
                  <Box sx={{ p: 3, bgcolor: 'rgba(255, 255, 255, 0.02)', borderRadius: '16px', border: '1px dashed rgba(255,255,255,0.08)', display: 'flex', flexDirection: 'column', gap: 2 }}>
                    <Typography variant="subtitle2" color="primary.main" sx={{ fontWeight: 700, display: 'flex', alignItems: 'center', gap: 1 }}>
                      <UserCheck size={16} /> ตั้งค่า OpenAPI Credentials
                    </Typography>
                    <TextField 
                      fullWidth
                      size="small"
                      label="App Key"
                      value={formAppKey}
                      onChange={(e) => setFormAppKey(e.target.value)}
                      disabled={actionLoading}
                    />
                    <TextField 
                      fullWidth
                      size="small"
                      label="App Secret"
                      type="password"
                      value={formAppSecret}
                      onChange={(e) => setFormAppSecret(e.target.value)}
                      disabled={actionLoading}
                    />
                  </Box>
                ) : formMode !== "LOCAL_PAPER" ? (
                  <Box sx={{ p: 3, bgcolor: 'rgba(255, 255, 255, 0.02)', borderRadius: '16px', border: '1px dashed rgba(255,255,255,0.08)', display: 'flex', flexDirection: 'column', gap: 2 }}>
                    <Typography variant="subtitle2" color="primary.main" sx={{ fontWeight: 700, display: 'flex', alignItems: 'center', gap: 1 }}>
                      <UserCheck size={16} /> ข้อมูลบัญชีผู้ใช้ Webull
                    </Typography>
                    <TextField 
                      fullWidth
                      size="small"
                      label="Username (เบอร์โทรหรืออีเมล)"
                      placeholder="+66-8xxxxxxxx หรือ user@email.com"
                      value={formUsername}
                      onChange={(e) => setFormUsername(e.target.value)}
                      disabled={actionLoading}
                    />
                    <TextField 
                      fullWidth
                      size="small"
                      label="Password"
                      type="password"
                      value={formPassword}
                      onChange={(e) => setFormPassword(e.target.value)}
                      disabled={actionLoading}
                    />
                    {formMode === "WEBULL_LIVE" && (
                      <TextField 
                        fullWidth
                        size="small"
                        label="Trade PIN (6 หลัก)"
                        type="password"
                        slotProps={{ htmlInput: { maxLength: 6 } }}
                        value={formTradePin}
                        onChange={(e) => setFormTradePin(e.target.value)}
                        disabled={actionLoading}
                      />
                    )}
                  </Box>
                ) : (
                  <Box sx={{ p: 3, bgcolor: 'rgba(255, 255, 255, 0.02)', borderRadius: '16px', border: '1px dashed rgba(255,255,255,0.08)', display: 'flex', flexDirection: 'column', gap: 2 }}>
                    <Typography variant="subtitle2" color="primary.main" sx={{ fontWeight: 700, display: 'flex', alignItems: 'center', gap: 1 }}>
                      💵 ตั้งค่าเงินจำลองเริ่มต้น (Local Paper Trading Cash)
                    </Typography>
                    <TextField 
                      fullWidth
                      size="small"
                      label="เงินจำลองเริ่มต้น USD (USD Starting Cash) - ระบบจะคำนวณเงิน HKD (7.8 เท่า) ให้โดยอัตโนมัติ"
                      type="number"
                      value={formSimulatedInitialCash}
                      onChange={(e) => {
                        const val = parseFloat(e.target.value) || 0;
                        setFormSimulatedInitialCash(val);
                        setFormSimulatedInitialCashHkd(Math.round(val * 7.8));
                      }}
                      disabled={actionLoading}
                    />
                  </Box>
                )}



                <Button 
                  type="submit" 
                  fullWidth
                  variant="contained"
                  color="primary"
                  disabled={actionLoading || !connected}
                  sx={{ 
                    boxShadow: '0 4px 20px rgba(0, 242, 254, 0.25)',
                    py: 1.5,
                    fontSize: '1rem'
                  }}
                >
                  {actionLoading ? <RefreshCw className="spin" size={18} /> : "บันทึกการตั้งค่าบอทและโหลดข้อมูลใหม่ (Save & Hot-Reload)"}
                </Button>

              </Box>
            </form>
          </CardContent>
        </Card>
        
    </>
  );
}
