"use client";

import React, { useEffect, useState, useCallback } from 'react';
import { 
  Box, 
  Typography, 
  Card, 
  CardContent, 
  Table, 
  TableBody, 
  TableCell, 
  TableContainer, 
  TableHead, 
  TableRow, 
  Paper,
  CircularProgress,
  Chip,
  Alert,
  AlertTitle,
  Switch,
  FormControlLabel,
  Tabs,
  Tab
} from '@mui/material';
import { 
  TrendingDown, 
  Info, 
  RefreshCw, 
  Database,
  AlertCircle,
  Wallet,
  TrendingUp,
  Cpu
} from 'lucide-react';
import { useToast } from 'frontend/components/ToastProvider';

const API_BASE = "http://127.0.0.1:8484/api";

interface ETFShortStatus {
  underlying: string;
  underlying_price: number;
  etf: string;
  etf_price: number;
  owned_qty: number;
  avg_price: number;
  market_value: number;
  unrealized_pnl: number;
}

export default function ETFShortPage() {
  const [mounted, setMounted] = useState(false);
  const [connected, setConnected] = useState(false);
  const [tradeMode, setTradeMode] = useState("LOCAL_PAPER");
  const [apiError, setApiError] = useState<string | null>(null);
  
  const [etfData, setEtfData] = useState<ETFShortStatus[]>([]);
  const [balance, setBalance] = useState({ cash: 0, cash_hkd: 0, net_liquidation: 0, net_liquidation_hkd: 0, currency: "USD", currency_hkd: "HKD" });
  const [status, setStatus] = useState<any>({ strategy_us: "sma", strategy_hk: "sma" });
  const [isLoading, setIsLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [tabIndex, setTabIndex] = useState(0);
  const { showToast } = useToast();

  const loadData = useCallback(async () => {
    try {
      const resStatus = await fetch(`${API_BASE}/status`);
      if (!resStatus.ok) throw new Error("Backend response error");
      const dataStatus = await resStatus.json();
      setTradeMode(dataStatus.trade_mode);
      setStatus(dataStatus);
      setConnected(true);
      setApiError(null);

      const resPort = await fetch(`${API_BASE}/portfolio`);
      if (resPort.ok) {
        const dataPort = await resPort.json();
        setBalance(dataPort.balance);
      }

      const resEtf = await fetch(`${API_BASE}/etf-short-status`);
      if (resEtf.ok) {
        const dataEtf = await resEtf.json();
        setEtfData(dataEtf);
      }
    } catch (err: any) {
      setConnected(false);
      setApiError(err.message || "Cannot connect to Python API server.");
    } finally {
      setIsLoading(false);
    }
  }, []);

  const handleToggleBot = async (market: "us" | "hk") => {
    setActionLoading(true);
    const isRunning = market === "us" 
      ? (status.running_us !== undefined ? status.running_us : status.running)
      : (status.running_hk !== undefined ? status.running_hk : status.running);
    const endpoint = isRunning ? "stop" : "start";
    try {
      const res = await fetch(`${API_BASE}/${endpoint}?market=${market}`, { method: "POST" });
      const data = await res.json();
      if (!res.ok) {
        showToast(`Error: ${data.detail || "Request failed"}`, "error");
      } else {
        showToast(`บอทหุ้น${market === "us" ? "สหรัฐฯ" : "ฮ่องกง"} ${isRunning ? 'หยุดทำงาน' : 'เริ่มทำงาน'}สำเร็จ`, "success");
        await loadData();
      }
    } catch (err) {
      showToast("Failed to toggle bot loop. Check backend console.", "error");
    } finally {
      setActionLoading(false);
    }
  };

  useEffect(() => {
    setMounted(true);
    loadData();
    const intervalId = setInterval(loadData, 3000);
    return () => clearInterval(intervalId);
  }, [loadData]);

  if (!mounted) {
    return null;
  }

  return (
    <Box sx={{ minHeight: '100vh', bgcolor: '#0b0f17', pb: 10 }}>


      {apiError && (
        <Alert 
          severity="error" 
          icon={<AlertCircle size={20} />}
          sx={{ mb: 4, borderRadius: '16px', border: '1px solid rgba(244, 63, 94, 0.2)', bgcolor: 'rgba(244, 63, 94, 0.05)' }}
        >
          <AlertTitle sx={{ fontWeight: 700 }}>ล้มเหลวในการเชื่อมต่อระบบหลังบ้าน</AlertTitle>
          ระบบขาดการติดต่อกับ Python API server (พอร์ต 8484)
        </Alert>
      )}

      {/* Top Metric Cards Panel */}
      <Box 
        sx={{ 
          display: 'grid', 
          gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr', md: '1fr 1fr 1fr 1fr' }, 
          gap: 3, 
          mb: 4 
        }}
      >
        {/* Card 1: Available Cash */}
        <Card sx={{ border: '1px solid rgba(255,255,255,0.05)', background: 'linear-gradient(135deg, rgba(15, 23, 42, 0.6) 0%, rgba(30, 41, 59, 0.6) 100%)' }}>
          <CardContent sx={{ p: 3 }}>
            <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 1.5 }}>
              <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600, letterSpacing: '0.5px' }}>
                ยอดเงินสดคงเหลือ
              </Typography>
              <Box sx={{ p: 1, borderRadius: '10px', bgcolor: 'rgba(59, 130, 246, 0.08)', display: 'flex' }}>
                <Wallet size={18} color="#3b82f6" />
              </Box>
            </Box>
            <Typography variant="h5" sx={{ fontWeight: 800, fontFamily: 'var(--font-mono)', mb: 0.5, color: '#f8fafc' }}>
              ${balance.cash.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </Typography>
            <Typography variant="body2" sx={{ fontWeight: 700, fontFamily: 'var(--font-mono)', color: '#94a3b8' }}>
              HK$ {balance.cash_hkd.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </Typography>
          </CardContent>
        </Card>

        {/* Card 2: Net Liquidation */}
        <Card sx={{ border: '1px solid rgba(255,255,255,0.05)', background: 'linear-gradient(135deg, rgba(15, 23, 42, 0.6) 0%, rgba(30, 41, 59, 0.6) 100%)' }}>
          <CardContent sx={{ p: 3 }}>
            <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 1.5 }}>
              <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600, letterSpacing: '0.5px' }}>
                มูลค่าพอร์ตรวม
              </Typography>
              <Box sx={{ p: 1, borderRadius: '10px', bgcolor: 'rgba(59, 130, 246, 0.08)', display: 'flex' }}>
                <TrendingUp size={18} color="#3b82f6" />
              </Box>
            </Box>
            <Typography variant="h5" sx={{ fontWeight: 800, fontFamily: 'var(--font-mono)', mb: 0.5, color: '#f8fafc' }}>
              ${balance.net_liquidation.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </Typography>
            <Typography variant="body2" sx={{ fontWeight: 700, fontFamily: 'var(--font-mono)', color: '#94a3b8' }}>
              HK$ {balance.net_liquidation_hkd.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </Typography>
          </CardContent>
        </Card>

        {/* Card 3: Unrealized Profit & Loss */}
        <Card sx={{ border: '1px solid rgba(255,255,255,0.05)', background: 'linear-gradient(135deg, rgba(15, 23, 42, 0.6) 0%, rgba(30, 41, 59, 0.6) 100%)' }}>
          <CardContent sx={{ p: 3 }}>
            {(() => {
              const totalPnlUsd = etfData.filter(d => !d.underlying.endsWith(".HK")).reduce((sum, d) => sum + d.unrealized_pnl, 0);
              const totalPnlHkd = etfData.filter(d => d.underlying.endsWith(".HK")).reduce((sum, d) => sum + d.unrealized_pnl, 0);
              const isProfit = (totalPnlUsd + totalPnlHkd) >= 0;
              return (
                <>
                  <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 1.5 }}>
                    <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600, letterSpacing: '0.5px' }}>
                      กำไรจำลองสะสม (ETF Short)
                    </Typography>
                    <Box sx={{ p: 1, borderRadius: '10px', bgcolor: isProfit ? 'rgba(16, 185, 129, 0.08)' : 'rgba(244, 63, 94, 0.08)', display: 'flex' }}>
                      {isProfit ? <TrendingUp size={18} color="#10b981" /> : <TrendingDown size={18} color="#f43f5e" />}
                    </Box>
                  </Box>
                  <Typography variant="h5" sx={{ fontWeight: 800, fontFamily: 'var(--font-mono)', mb: 0.5, color: totalPnlUsd >= 0 ? '#10b981' : '#ef4444' }}>
                    {totalPnlUsd >= 0 ? "+" : ""}${totalPnlUsd.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </Typography>
                  <Typography variant="body2" sx={{ fontWeight: 700, fontFamily: 'var(--font-mono)', color: totalPnlHkd >= 0 ? '#10b981' : '#ef4444' }}>
                    HK$ {totalPnlHkd >= 0 ? "+" : ""}{totalPnlHkd.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </Typography>
                </>
              );
            })()}
          </CardContent>
        </Card>

        {/* Card 4: Bot Control Panel */}
        <Card sx={{ border: '1px solid rgba(255,255,255,0.05)', background: 'linear-gradient(135deg, rgba(15, 23, 42, 0.6) 0%, rgba(30, 41, 59, 0.6) 100%)' }}>
          <CardContent sx={{ p: 3 }}>
            <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 1.5 }}>
              <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600, letterSpacing: '0.5px' }}>
                สถานะการควบคุมบอท
              </Typography>
              <Box sx={{ p: 1, borderRadius: '10px', bgcolor: 'rgba(59, 130, 246, 0.08)', display: 'flex' }}>
                <Cpu size={18} color="#3b82f6" />
              </Box>
            </Box>

            {/* US Bot Row */}
            <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 1 }}>
              <Box>
                <Typography variant="body2" sx={{ fontWeight: 700, color: (status.running_us !== undefined ? status.running_us : status.running) ? "success.main" : "text.secondary" }}>
                  US Bot: {(status.running_us !== undefined ? status.running_us : status.running) ? "RUNNING" : "STANDBY"}
                </Typography>
                <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.7rem' }}>
                  กลยุทธ์: {(status.strategy_us || "SMA").toUpperCase()}
                </Typography>
              </Box>
              <FormControlLabel
                control={
                  <Switch 
                    checked={status.running_us !== undefined ? status.running_us : status.running} 
                    onChange={() => handleToggleBot("us")}
                    color="success"
                    disabled={actionLoading || !connected}
                    size="small"
                  />
                }
                label=""
                sx={{ mr: 0 }}
              />
            </Box>

            {/* HK Bot Row */}
            <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <Box>
                <Typography variant="body2" sx={{ fontWeight: 700, color: (status.running_hk !== undefined ? status.running_hk : status.running) ? "success.main" : "text.secondary" }}>
                  HK Bot: {(status.running_hk !== undefined ? status.running_hk : status.running) ? "RUNNING" : "STANDBY"}
                </Typography>
                <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.7rem' }}>
                  กลยุทธ์: {(status.strategy_hk || "SMA").toUpperCase()}
                </Typography>
              </Box>
              <FormControlLabel
                control={
                  <Switch 
                    checked={status.running_hk !== undefined ? status.running_hk : status.running} 
                    onChange={() => handleToggleBot("hk")}
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

      {/* 2. Page Description Card (Minimal) */}
      <Box sx={{ 
        mb: 4, 
        p: 2, 
        borderRadius: '12px', 
        bgcolor: 'rgba(30, 41, 59, 0.4)', 
        border: '1px solid rgba(255,255,255,0.05)',
        display: 'flex',
        alignItems: 'center',
        gap: 1.5
      }}>
        <Info size={18} color="#60a5fa" style={{ flexShrink: 0 }} />
        <Typography variant="body2" color="text.secondary">
          <strong>Inverse ETF (ETF ขาลง):</strong> ระบบจะจับคู่หุ้นปกติ (Underlying) เข้ากับ Inverse ETF เพื่อทำกำไรเมื่อตลาดเข้าสู่แนวโน้มขาลง เป็นทางเลือกที่ปลอดภัย ไม่ต้องยืมหุ้น, ไม่มีค่าธรรมเนียมกู้ยืม และจำกัดความเสี่ยงสูงสุด
        </Typography>
      </Box>

      {/* 3. ETF Pricing and Holdings Table */}
      <Card sx={{ background: 'linear-gradient(135deg, rgba(15, 23, 42, 0.8) 0%, rgba(30, 41, 59, 0.8) 100%)', border: '1px solid rgba(255,255,255,0.05)', borderRadius: '16px' }}>
        <CardContent sx={{ p: 4 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="subtitle1" sx={{ fontWeight: 700, display: 'flex', alignItems: 'center', gap: 1 }}>
              <Database size={18} color="#3b82f6" /> รายการจับคู่และสถานะการลงทุนใน Inverse ETF
            </Typography>
            {isLoading && <CircularProgress size={20} color="primary" />}
          </Box>

          <Box sx={{ borderBottom: 1, borderColor: 'rgba(255,255,255,0.08)', mb: 3 }}>
            <Tabs 
              value={tabIndex} 
              onChange={(e, newIdx) => setTabIndex(newIdx)} 
              textColor="primary" 
              indicatorColor="primary"
            >
              <Tab label="🇺🇸 ETF สหรัฐฯ (Traded in USD)" sx={{ fontWeight: 700, textTransform: 'none' }} />
              <Tab label="🇭🇰 ETF ฮ่องกง (Traded in HKD)" sx={{ fontWeight: 700, textTransform: 'none' }} />
            </Tabs>
          </Box>

          <TableContainer component={Paper} sx={{ bgcolor: 'transparent', boxShadow: 'none', backgroundImage: 'none' }}>
            <Table sx={{ minWidth: 650 }}>
              <TableHead sx={{ bgcolor: 'rgba(255,255,255,0.02)' }}>
                <TableRow>
                  <TableCell sx={{ color: 'text.secondary', fontWeight: 700 }}>หุ้นหลัก (Underlying)</TableCell>
                  <TableCell sx={{ color: 'text.secondary', fontWeight: 700 }} align="right">ราคาหุ้นหลัก</TableCell>
                  <TableCell sx={{ color: 'text.secondary', fontWeight: 700 }}>Inverse ETF</TableCell>
                  <TableCell sx={{ color: 'text.secondary', fontWeight: 700 }} align="right">ราคา ETF</TableCell>
                  <TableCell sx={{ color: 'text.secondary', fontWeight: 700 }} align="right">จำนวนที่ถือครอง</TableCell>
                  <TableCell sx={{ color: 'text.secondary', fontWeight: 700 }} align="right">ราคาเฉลี่ย</TableCell>
                  <TableCell sx={{ color: 'text.secondary', fontWeight: 700 }} align="right">มูลค่ารวม</TableCell>
                  <TableCell sx={{ color: 'text.secondary', fontWeight: 700 }} align="right">กำไร / ขาดทุนสะสม</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {etfData
                  .filter((row) => {
                    const isHk = row.underlying.endsWith(".HK");
                    return tabIndex === 0 ? !isHk : isHk;
                  })
                  .map((row) => {
                    const hasPosition = row.owned_qty > 0;
                    const isProfit = row.unrealized_pnl >= 0;
                    const isHk = row.underlying.endsWith(".HK");
                    const currency = isHk ? "HKD" : "USD";
                    const currencySign = isHk ? "HK$" : "$";
                    
                    return (
                      <TableRow key={row.underlying} sx={{ '&:hover': { bgcolor: 'rgba(255,255,255,0.01)' } }}>
                        <TableCell sx={{ fontWeight: 700, color: '#f1f5f9' }}>
                          {row.underlying}
                        </TableCell>
                        <TableCell align="right" sx={{ fontFamily: 'var(--font-mono)', fontWeight: 600 }}>
                          {currencySign}{row.underlying_price.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                        </TableCell>
                        <TableCell sx={{ fontWeight: 700, color: '#60a5fa' }}>
                          {row.etf}
                        </TableCell>
                        <TableCell align="right" sx={{ fontFamily: 'var(--font-mono)', fontWeight: 600, color: '#60a5fa' }}>
                          {currencySign}{row.etf_price.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                        </TableCell>
                        <TableCell align="right" sx={{ fontFamily: 'var(--font-mono)', fontWeight: 600 }}>
                          {hasPosition ? (
                            <Chip label={`${row.owned_qty} หุ้น`} size="small" color="primary" sx={{ fontWeight: 700, borderRadius: '6px' }} />
                          ) : (
                            <Typography variant="body2" color="text.secondary">-</Typography>
                          )}
                        </TableCell>
                        <TableCell align="right" sx={{ fontFamily: 'var(--font-mono)' }}>
                          {hasPosition ? `${currencySign}${row.avg_price.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : "-"}
                        </TableCell>
                        <TableCell align="right" sx={{ fontFamily: 'var(--font-mono)', fontWeight: 700 }}>
                          {hasPosition ? `${currencySign}${row.market_value.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : "-"}
                        </TableCell>
                        <TableCell align="right" sx={{ fontFamily: 'var(--font-mono)', fontWeight: 700, color: isProfit ? '#10b981' : '#ef4444' }}>
                          {hasPosition ? (
                            <>
                              {isProfit ? "+" : ""}
                              {row.unrealized_pnl.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })} {currency}
                            </>
                          ) : (
                            "-"
                          )}
                        </TableCell>
                      </TableRow>
                    );
                  })}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>
    </Box>
  );
}
