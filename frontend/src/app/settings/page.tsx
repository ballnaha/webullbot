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
  AlertTitle
} from '@mui/material';

import Header from 'frontend/components/Header';

import { 
  Settings, 
  UserCheck, 
  RefreshCw, 
  AlertCircle
} from 'lucide-react';

const API_BASE = "http://127.0.0.1:8484/api";

interface BotStatus {
  running: boolean;
  trade_mode: string;
  strategy: string;
  symbols: string[];
  quantity: number;
  interval: number;
  candle_period: string;
  has_client: boolean;
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
  const [mounted, setMounted] = useState(false);
  const [connected, setConnected] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState(false);

  // Status state
  const [status, setStatus] = useState<BotStatus>({
    running: false,
    trade_mode: "LOCAL_PAPER",
    strategy: "sma",
    symbols: [],
    quantity: 1,
    interval: 60,
    candle_period: "m5",
    has_client: false
  });

  // Config form state
  const [formMode, setFormMode] = useState("LOCAL_PAPER");
  const [formUsSymbols, setFormUsSymbols] = useState("");
  const [formHkSymbols, setFormHkSymbols] = useState("");
  const [formQty, setFormQty] = useState(1);
  const [formInterval, setFormInterval] = useState(60);
  const [formPeriod, setFormPeriod] = useState("m5");
  const [formStrategy, setFormStrategy] = useState("sma");
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
    if (!isConfigInitialized && status.symbols.length > 0) {
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
        alert(`Config Save Error: ${data.detail || "Validation failed"}`);
      } else {
        alert("Configuration saved and hot-reloaded successfully!");
        setIsConfigInitialized(false); // Unlock to sync
        setFormUsername("");
        setFormPassword("");
        setFormTradePin("");
        setFormAppKey("");
        setFormAppSecret("");
        await loadData();
      }
    } catch (err) {
      alert("Failed to update config. Backend might be reinitializing.");
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
                ) : null}

                {/* 3. Strategy */}
                <FormControl fullWidth size="small">
                  <InputLabel>กลยุทธ์ส่งสัญญาณ (Strategy)</InputLabel>
                  <Select
                    value={formStrategy}
                    label="กลยุทธ์ส่งสัญญาณ (Strategy)"
                    onChange={(e) => setFormStrategy(e.target.value)}
                    disabled={actionLoading}
                    sx={{ borderRadius: '12px' }}
                  >
                    <MenuItem value="sma">SMA Crossover (ตัดกันระยะสั้น/ยาว)</MenuItem>
                    <MenuItem value="rsi">RSI Reversal (สัญญาณกลับตัว RSI)</MenuItem>
                    <MenuItem value="hybrid">SMA+RSI Hybrid (กลยุทธ์ผสมสแกนแม่นยำ)</MenuItem>
                  </Select>
                </FormControl>

                {/* 4. Watchlists US and HK */}
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2.5 }}>
                  <TextField 
                    fullWidth
                    size="small"
                    label="รายชื่อหุ้นตลาดสหรัฐฯ US Tickers (คั่นด้วยเครื่องหมายจุลภาค ,)"
                    placeholder="เช่น AAPL, TSLA, NVDA"
                    value={formUsSymbols}
                    onChange={(e) => setFormUsSymbols(e.target.value)}
                    disabled={actionLoading}
                  />

                  <TextField 
                    fullWidth
                    size="small"
                    label="รายชื่อหุ้นตลาดฮ่องกง HK Tickers (คั่นด้วยเครื่องหมายจุลภาค ,)"
                    placeholder="เช่น 0700, 9988, 1810"
                    value={formHkSymbols}
                    onChange={(e) => setFormHkSymbols(e.target.value)}
                    disabled={actionLoading}
                    helperText="ป้อนเฉพาะเลขรหัสหุ้นฮ่องกงได้ บอทจะเติมนามสกุล .HK ให้โดยอัตโนมัติ"
                  />
                </Box>

                {/* 5. Parameters grid */}
                <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr' }, gap: 2.5 }}>
                  <TextField 
                    fullWidth
                    size="small"
                    label="จำนวนสั่งซื้อมาตรฐาน (Qty)"
                    type="number"
                    value={formQty}
                    onChange={(e) => setFormQty(parseInt(e.target.value) || 1)}
                    slotProps={{ htmlInput: { min: 1 } }}
                    required
                    disabled={actionLoading}
                  />

                  <FormControl fullWidth size="small">
                    <InputLabel>ช่วงเวลาแท่งเทียน (Candle Period)</InputLabel>
                    <Select
                      value={formPeriod}
                      label="ช่วงเวลาแท่งเทียน (Candle Period)"
                      onChange={(e) => setFormPeriod(e.target.value)}
                      disabled={actionLoading}
                      sx={{ borderRadius: '12px' }}
                    >
                      <MenuItem value="m1">1 นาที (1m)</MenuItem>
                      <MenuItem value="m5">5 นาที (5m)</MenuItem>
                      <MenuItem value="m15">15 นาที (15m)</MenuItem>
                      <MenuItem value="m30">30 นาที (30m)</MenuItem>
                      <MenuItem value="h1">1 ชั่วโมง (1h)</MenuItem>
                      <MenuItem value="d">1 วัน (1d)</MenuItem>
                    </Select>
                  </FormControl>
                </Box>

                {/* 6. Scan speed */}
                <TextField 
                  fullWidth
                  size="small"
                  label="ความถี่ในการอัปเดตสแกนของบอทหลังบ้าน (หน่วยวินาที)"
                  type="number"
                  value={formInterval}
                  onChange={(e) => setFormInterval(parseInt(e.target.value) || 60)}
                  slotProps={{ htmlInput: { min: 10 } }}
                  required
                  disabled={actionLoading}
                />

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
