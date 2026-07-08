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
  Box, 
  Alert, 
  AlertTitle,
  Table, 
  TableBody, 
  TableCell, 
  TableContainer, 
  TableHead, 
  TableRow,
  Chip
} from '@mui/material';

import Header from 'frontend/components/Header';

import { 
  Terminal, 
  History, 
  AlertCircle,
  Clock
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

interface Trade {
  time: string;
  symbol: string;
  action: string;
  qty: number;
  price: number;
  status: string;
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

export default function LogsPage() {
  const [mounted, setMounted] = useState(false);
  const [connected, setConnected] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);

  // Status & logs state
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
  const [logs, setLogs] = useState<string[]>([]);
  const [trades, setTrades] = useState<Trade[]>([]);

  const loadData = useCallback(async () => {
    try {
      const resStatus = await fetch(`${API_BASE}/status`);
      if (!resStatus.ok) throw new Error("Backend response error");
      const dataStatus = await resStatus.json();
      setStatus(dataStatus);
      setConnected(true);
      setApiError(null);

      const resHistory = await fetch(`${API_BASE}/history`);
      if (resHistory.ok) {
        const dataHistory = await resHistory.json();
        setLogs(dataHistory.logs);
        setTrades(dataHistory.trades);
      }
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

  return (
    <>

        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
          
          {/* Section 1: System logs console */}
          <Card>
            <CardContent sx={{ p: 3.5 }}>
              <Box sx={{ display: "flex", alignItems: "center", gap: 1.5, mb: 3.5 }}>
                <Box sx={{ p: 1, borderRadius: '10px', bgcolor: 'rgba(59, 130, 246, 0.08)', display: 'flex' }}>
                  <Terminal size={20} color="#3b82f6" />
                </Box>
                <Box>
                  <Typography variant="h6" sx={{ fontWeight: 800 }}>
                    คอนโซลบันทึกกิจกรรมบอท (System Activity Logs)
                  </Typography>
                  <Typography variant="caption" color="text.secondary">ความเคลื่อนไหว กิจกรรมการสแกนสัญญาณเทรด และการซื้อขายล่าสดจากระบบ</Typography>
                </Box>
              </Box>

              <Box 
                sx={{
                  bgcolor: '#04060b',
                  border: '1px solid rgba(255, 255, 255, 0.05)',
                  borderRadius: '12px',
                  p: 3,
                  maxHeight: 450,
                  height: 450,
                  overflowY: 'auto',
                  fontFamily: 'var(--font-mono)',
                  fontSize: '0.82rem',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 1.5,
                  // Re-style scrollbar
                  '&::-webkit-scrollbar': {
                    width: '8px',
                  },
                  '&::-webkit-scrollbar-track': {
                    background: 'rgba(0,0,0,0.1)',
                  },
                  '&::-webkit-scrollbar-thumb': {
                    background: 'rgba(59, 130, 246, 0.2)',
                    borderRadius: '4px',
                    '&:hover': {
                      background: 'rgba(59, 130, 246, 0.4)'
                    }
                  }
                }}
              >
                {logs.length === 0 ? (
                  <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic' }}>
                    ไม่มีประวัติบันทึกกิจกรรม...
                  </Typography>
                ) : (
                  [...logs].reverse().map((log, idx) => {
                    let color = '#94a3b8';
                    const lower = log.toLowerCase();
                    if (lower.includes('[system]')) color = '#3b82f6';
                    else if (lower.includes('success') || lower.includes('bought')) color = '#16c784';
                    else if (lower.includes('failed') || lower.includes('sold')) color = '#ea3943';
                    else if (lower.includes('warning')) color = '#f0a020';
                    
                    return (
                      <Box key={idx} sx={{ color, lineHeight: 1.5, wordBreak: 'break-all' }}>
                        {log}
                      </Box>
                    );
                  })
                )}
              </Box>
            </CardContent>
          </Card>

          {/* Section 2: Trades history */}
          <Card>
            <CardContent sx={{ p: 0, '&:last-child': { pb: 0 } }}>
              <Box sx={{ p: 3.5, display: "flex", alignItems: "center", gap: 1.5 }}>
                <Box sx={{ p: 1, borderRadius: '10px', bgcolor: 'rgba(99, 102, 241, 0.08)', display: 'flex' }}>
                  <History size={20} color="#6366f1" />
                </Box>
                <Box>
                  <Typography variant="h6" sx={{ fontWeight: 800 }}>
                    ประวัติรายการส่งคำสั่งซื้อขาย (Order Transmission History)
                  </Typography>
                  <Typography variant="caption" color="text.secondary">ตรวจสอบประวัติรายการออเดอร์เข้าซื้อหรือขายจากสแกนเนอร์บอท</Typography>
                </Box>
              </Box>

              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>เวลาทำรายการ (Time)</TableCell>
                      <TableCell>หุ้น (Ticker)</TableCell>
                      <TableCell align="center">ประเภทคำสั่ง</TableCell>
                      <TableCell align="right">จำนวนหุ้น (Qty)</TableCell>
                      <TableCell align="right">ราคาเป้าหมาย (Price)</TableCell>
                      <TableCell align="center">สถานะออเดอร์</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {trades.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={6} align="center" sx={{ py: 6, color: 'text.secondary' }}>
                          ไม่มีประวัติออเดอร์การซื้อขายในระบบในขณะนี้
                        </TableCell>
                      </TableRow>
                    ) : (
                      [...trades].reverse().map((trade, idx) => {
                        const isBuy = trade.action === "BUY";
                        return (
                          <TableRow key={idx} hover sx={{ '&:hover': { bgcolor: 'rgba(255,255,255,0.02)' } }}>
                            <TableCell sx={{ py: 1.5, display: 'flex', alignItems: 'center', gap: 1, color: 'text.secondary', fontSize: '0.85rem' }}>
                              <Clock size={12} /> {trade.time}
                            </TableCell>
                            <TableCell sx={{ py: 1.5, fontWeight: 700, color: 'primary.main' }}>
                              {trade.symbol}
                            </TableCell>
                            <TableCell align="center" sx={{ py: 1.5 }}>
                              <Chip 
                                label={trade.action}
                                size="small"
                                color={isBuy ? "success" : "error"}
                                sx={{ fontWeight: 800, fontSize: '0.7rem', height: 20, borderRadius: '6px' }}
                              />
                            </TableCell>
                            <TableCell align="right" sx={{ py: 1.5, fontFamily: 'var(--font-mono)', fontWeight: 600 }}>{trade.qty}</TableCell>
                            <TableCell align="right" sx={{ py: 1.5, fontFamily: 'var(--font-mono)' }}>${trade.price.toFixed(2)}</TableCell>
                            <TableCell align="center" sx={{ py: 1.5 }}>
                              <Typography variant="body2" sx={{ fontWeight: 700, color: trade.status.toLowerCase() === "filled" ? 'success.main' : 'text.secondary' }}>
                                {trade.status.toUpperCase()}
                              </Typography>
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
    </>
  );
}
