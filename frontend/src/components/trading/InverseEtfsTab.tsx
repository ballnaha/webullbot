import React, { useState } from 'react';
import { 
  Table, 
  TableBody, 
  TableCell, 
  TableContainer, 
  TableHead, 
  TableRow,
  Typography,
  Box,
  Button,
  Chip,
  TablePagination,
  CircularProgress
} from '@mui/material';
import { SignalData } from './types';

interface InverseEtfsTabProps {
  market: 'US' | 'HK';
  etfData: any[];
  signals: SignalData[];
  onQuickTrade: (symbol: string, action: 'BUY' | 'SELL', defaultQty?: number) => void | Promise<void>;
  actionLoading: boolean;
  connected: boolean;
  isSignalsLoading: boolean;
  hasClient: boolean;
  stockNames: Record<string, string>;
  hkEtfQty?: number;
  hkEtfStrategy?: string;
}

export const InverseEtfsTab: React.FC<InverseEtfsTabProps> = React.memo(({
  market,
  etfData,
  signals,
  onQuickTrade,
  actionLoading,
  connected,
  isSignalsLoading,
  hasClient,
  stockNames,
  hkEtfQty,
  hkEtfStrategy
}) => {
  const [pageEtf, setPageEtf] = useState(0);
  const [rowsPerPageEtf, setRowsPerPageEtf] = useState(10);

  const currencyPrefix = market === 'HK' ? 'HK$ ' : '$';

  return (
    <>
      <Box sx={{ px: 3, py: 2, bgcolor: 'rgba(255,255,255,0.01)', borderBottom: '1px solid rgba(255,255,255,0.03)' }}>
        <Typography variant="caption" sx={{ color: 'text.secondary', fontWeight: 500 }}>
          📉 คู่ป้องกัน <span style={{ color: '#f43f5e', fontWeight: 700 }}>{etfData.length}</span> คู่ &mdash; สัญญาณ <span style={{ fontWeight: 600 }}>กลับทิศ</span>: หุ้นหลัก SELL = ETF ควร BUY
        </Typography>
      </Box>
      <TableContainer>
        <Table size="small">
          <TableHead sx={{ bgcolor: 'rgba(255,255,255,0.02)' }}>
            <TableRow>
              <TableCell sx={{ fontWeight: 700, color: '#94a3b8', borderBottom: '1px solid rgba(255,255,255,0.08)', py: 1.5, fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em', width: '22%' }}>Inverse ETF / หุ้นหลัก</TableCell>
              <TableCell align="right" sx={{ fontWeight: 700, color: '#94a3b8', borderBottom: '1px solid rgba(255,255,255,0.08)', py: 1.5, fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em', width: '12%' }}>ราคา ETF</TableCell>
              <TableCell align="left" sx={{ pl: 4, fontWeight: 700, color: '#94a3b8', borderBottom: '1px solid rgba(255,255,255,0.08)', py: 1.5, fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em', width: '24%' }}>สัญญาณหุ้นหลัก (Indicators)</TableCell>
              <TableCell align="center" sx={{ fontWeight: 700, color: '#94a3b8', borderBottom: '1px solid rgba(255,255,255,0.08)', py: 1.5, fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em', width: '27%' }}>แนะนำ ETF / สถานะพอร์ต</TableCell>
              <TableCell align="center" sx={{ fontWeight: 700, color: '#94a3b8', borderBottom: '1px solid rgba(255,255,255,0.08)', py: 1.5, fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em', width: '15%' }}>ซื้อขายด่วน (Quick Trade)</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {isSignalsLoading && etfData.length === 0 ? (
              <TableRow>
                <TableCell colSpan={5} align="center" sx={{ py: 6 }}>
                  <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 1.5, py: 2 }}>
                    <CircularProgress size={24} color="secondary" />
                    <Typography variant="body2" color="text.secondary">กำลังโหลดข้อมูลจับคู่และราคากองทุน Inverse ETF...</Typography>
                  </Box>
                </TableCell>
              </TableRow>
            ) : etfData.length === 0 ? (
              <TableRow>
                <TableCell colSpan={5} align="center" sx={{ py: 6, color: 'text.secondary' }}>
                  ไม่มีข้อมูล Inverse ETF สำหรับตลาดนี้
                </TableCell>
              </TableRow>
            ) : (
              etfData
                .slice(pageEtf * rowsPerPageEtf, pageEtf * rowsPerPageEtf + rowsPerPageEtf)
                .map((row) => {
                  const hasPosition = row.owned_qty > 0;
                  const isProfit = row.unrealized_pnl >= 0;
                  const underlyingSig = signals.find(s => s.symbol === row.underlying);
                  const strategyToUse = hkEtfStrategy || "all";
                  
                  let confData = { label: 'NEUTRAL / HOLD', desc: 'ไม่มีทิศทางชัดเจน', bgcolor: 'rgba(148,163,184,0.05)', textcolor: '#94a3b8', border: '1px solid rgba(148,163,184,0.15)' };
                  
                  if (strategyToUse === "all") {
                    // Invert underlying signal → ETF recommendation
                    const smaScore = underlyingSig ? (underlyingSig.sma_signal === 'SELL' ? 1 : underlyingSig.sma_signal === 'BUY' ? -1 : 0) : 0;
                    const rsiScore = underlyingSig ? (underlyingSig.rsi_signal === 'SELL' ? 1 : underlyingSig.rsi_signal === 'BUY' ? -1 : 0) : 0;
                    const hybScore = underlyingSig ? (underlyingSig.hybrid_signal === 'SELL' ? 1 : underlyingSig.hybrid_signal === 'BUY' ? -1 : 0) : 0;
                    const etfScore = smaScore + rsiScore + hybScore;
                    
                    confData = etfScore === 3
                      ? { label: 'BUY ETF (3/3)', desc: 'มติเอกฉันท์ขาลง — ซื้อ ETF ทันที', bgcolor: 'rgba(22, 199, 132, 0.15)', textcolor: '#16c784', border: '1px solid #16c784' }
                      : etfScore === 2
                      ? { label: '67% BUY ETF', desc: 'แนวโน้ม ETF ขึ้นแข็งแกร่ง (2/3)', bgcolor: 'rgba(22, 199, 132, 0.08)', textcolor: '#16c784', border: '1px dashed rgba(22,199,132,0.5)' }
                      : etfScore === 1
                      ? { label: '33% BUY ETF', desc: 'สัญญาณซื้อ ETF อ่อน (1/3)', bgcolor: 'transparent', textcolor: '#16c784', border: '1px solid rgba(22,199,132,0.25)' }
                      : etfScore === -3
                      ? { label: 'SELL ETF (3/3)', desc: 'หุ้นหลักขึ้น — ขาย ETF ออก', bgcolor: 'rgba(234, 57, 67, 0.15)', textcolor: '#ea3943', border: '1px solid #ea3943' }
                      : etfScore === -2
                      ? { label: '67% SELL ETF', desc: 'ETF อ่อนแอ ระวังการถือ (2/3)', bgcolor: 'rgba(234, 57, 67, 0.08)', textcolor: '#ea3943', border: '1px dashed rgba(234,57,67,0.5)' }
                      : etfScore === -1
                      ? { label: '33% SELL ETF', desc: 'สัญญาณขาย ETF อ่อน (1/3)', bgcolor: 'transparent', textcolor: '#ea3943', border: '1px solid rgba(234,57,67,0.25)' }
                      : { label: 'NEUTRAL / HOLD', desc: 'ไม่มีทิศทางชัดเจน', bgcolor: 'rgba(148,163,184,0.05)', textcolor: '#94a3b8', border: '1px solid rgba(148,163,184,0.15)' };
                  } else {
                    let sigVal = "";
                    if (strategyToUse === "sma") sigVal = underlyingSig?.sma_signal || "";
                    else if (strategyToUse === "rsi") sigVal = underlyingSig?.rsi_signal || "";
                    else if (strategyToUse === "hybrid") sigVal = underlyingSig?.hybrid_signal || "";
                    else if (strategyToUse === "volume_ema") sigVal = underlyingSig?.volume_ema_signal || "";
                    
                    const displaySig = sigVal || "HOLD";
                    if (displaySig === "SELL") {
                      confData = { label: 'BUY ETF (100%)', desc: 'สัญญาณยืนยันหุ้นหลักขาลง — ซื้อ ETF', bgcolor: 'rgba(22, 199, 132, 0.15)', textcolor: '#16c784', border: '1px solid #16c784' };
                    } else if (displaySig === "BUY") {
                      confData = { label: 'SELL ETF (100%)', desc: 'สัญญาณยืนยันหุ้นหลักขาขึ้น — ขาย ETF', bgcolor: 'rgba(234, 57, 67, 0.15)', textcolor: '#ea3943', border: '1px solid #ea3943' };
                    } else {
                      confData = { label: 'NEUTRAL / HOLD', desc: `บอทส่งสัญญาณ ${displaySig} — ถือเงินสด`, bgcolor: 'rgba(148,163,184,0.05)', textcolor: '#94a3b8', border: '1px solid rgba(148,163,184,0.15)' };
                    }
                  }
                  
                  const pnlPct = hasPosition && row.avg_price > 0 ? (row.unrealized_pnl / (row.avg_price * row.owned_qty) * 100) : null;
                  
                  return (
                    <TableRow key={row.underlying} hover sx={{ '&:hover': { bgcolor: 'rgba(255,255,255,0.02)' } }}>
                      {/* Col 1: ETF primary + underlying subtitle */}
                      <TableCell sx={{ py: 1.5 }}>
                        <Typography sx={{ fontWeight: 800, color: 'secondary.main', fontSize: '0.9rem', lineHeight: 1.1 }}>
                          {row.etf}
                        </Typography>
                        <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.72rem', display: 'block', mt: 0.2 }}>
                          {stockNames[row.etf] || 'Inverse Hedge ETF'}
                        </Typography>
                        <Box sx={{ display: 'inline-flex', alignItems: 'center', gap: 0.5, mt: 0.4, px: 0.8, py: 0.2, bgcolor: 'rgba(59,130,246,0.07)', borderRadius: '4px', border: '1px solid rgba(59,130,246,0.15)' }}>
                          <Typography sx={{ fontSize: '0.65rem', fontWeight: 700, color: 'primary.main' }}>
                            ↑ {row.underlying}
                          </Typography>
                          <Typography sx={{ fontSize: '0.65rem', color: '#64748b' }}>
                            {currencyPrefix}{row.underlying_price.toFixed(2)}
                          </Typography>
                        </Box>
                      </TableCell>
                      {/* Col 2: ETF price */}
                      <TableCell align="right" sx={{ fontFamily: 'var(--font-mono)', fontWeight: 600, fontSize: '0.88rem' }}>
                        {currencyPrefix}{row.etf_price.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                      </TableCell>
                      {/* Col 3: Underlying indicators */}
                      <TableCell align="left" sx={{ pl: 4, py: 1.5 }}>
                        {underlyingSig ? (
                          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.4 }}>
                            <Box sx={{ display: 'flex', gap: 0.6, flexWrap: 'wrap', rowGap: 0.6 }}>
                              <Chip 
                                label={`SMA: ${underlyingSig.sma_signal}`} 
                                size="small" 
                                color={underlyingSig.sma_signal === 'SELL' ? 'error' : underlyingSig.sma_signal === 'BUY' ? 'success' : 'default'} 
                                variant={strategyToUse === 'sma' ? 'filled' : 'outlined'} 
                                sx={{ height: 20, fontSize: '0.68rem', fontWeight: 600, border: strategyToUse === 'sma' ? '1px solid #6366f1' : undefined }} 
                              />
                              <Chip 
                                label={`RSI: ${underlyingSig.rsi_signal}`} 
                                size="small" 
                                color={underlyingSig.rsi_signal === 'SELL' ? 'error' : underlyingSig.rsi_signal === 'BUY' ? 'success' : 'default'} 
                                variant={strategyToUse === 'rsi' ? 'filled' : 'outlined'} 
                                sx={{ height: 20, fontSize: '0.68rem', fontWeight: 600, border: strategyToUse === 'rsi' ? '1px solid #6366f1' : undefined }} 
                              />
                              <Chip 
                                label={`HYB: ${underlyingSig.hybrid_signal}`} 
                                size="small" 
                                color={underlyingSig.hybrid_signal === 'SELL' ? 'error' : underlyingSig.hybrid_signal === 'BUY' ? 'success' : 'default'} 
                                variant={strategyToUse === 'hybrid' ? 'filled' : 'outlined'} 
                                sx={{ height: 20, fontSize: '0.68rem', fontWeight: 600, border: strategyToUse === 'hybrid' ? '1px solid #6366f1' : undefined }} 
                              />
                              <Chip 
                                label={`V+EMA: ${underlyingSig.volume_ema_signal || 'HOLD'}`} 
                                size="small" 
                                color={(underlyingSig.volume_ema_signal || 'HOLD') === 'SELL' ? 'error' : (underlyingSig.volume_ema_signal || 'HOLD') === 'BUY' ? 'success' : 'default'} 
                                variant={strategyToUse === 'volume_ema' ? 'filled' : 'outlined'} 
                                sx={{ height: 20, fontSize: '0.68rem', fontWeight: 600, border: strategyToUse === 'volume_ema' ? '1px solid #6366f1' : undefined }} 
                              />
                            </Box>
                            <Typography variant="caption" sx={{ fontSize: '0.7rem', fontFamily: 'var(--font-mono)', color: 'text.secondary' }}>
                              RSI {underlyingSig.rsi.toFixed(1)} &nbsp;|&nbsp; SMA {underlyingSig.sma_fast > 0 ? `${currencyPrefix}${underlyingSig.sma_fast.toFixed(2)}` : 'N/A'}
                            </Typography>
                          </Box>
                        ) : (
                          <Typography variant="caption" sx={{ color: '#475569', fontStyle: 'italic' }}>ไม่มีข้อมูล — เพิ่ม {row.underlying} ใน Watchlist</Typography>
                        )}
                      </TableCell>
                      {/* Col 4: ETF recommendation / status */}
                      <TableCell align="center" sx={{ py: 1.5 }}>
                        <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 0.6 }}>
                          <Box sx={{
                            display: 'inline-block', px: 1.5, py: 0.5, borderRadius: '6px',
                            bgcolor: confData.bgcolor, color: confData.textcolor, border: confData.border,
                            fontWeight: 800, fontSize: '0.75rem', letterSpacing: '0.02em',
                            boxShadow: confData.label.includes('3/3') ? `0 0 12px ${confData.textcolor}20` : 'none'
                          }}>
                            {confData.label}
                          </Box>
                          <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.68rem' }}>
                            {confData.desc}
                          </Typography>
                          
                          {/* Active position badge */}
                          {hasPosition && (
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 0.4 }}>
                              <Typography variant="caption" sx={{ color: 'text.secondary', fontWeight: 600 }}>
                                ถืออยู่: <span style={{ color: '#fff', fontWeight: 700 }}>{row.owned_qty} หุ้น</span> (ทุน {currencyPrefix}{row.avg_price.toFixed(2)})
                              </Typography>
                              <Typography variant="caption" sx={{
                                color: isProfit ? 'success.main' : 'error.main',
                                fontWeight: 800,
                                bgcolor: isProfit ? 'rgba(22, 199, 132, 0.08)' : 'rgba(234, 57, 67, 0.08)',
                                px: 1, py: 0.2, borderRadius: '4px', border: `1px solid ${isProfit ? 'rgba(22, 199, 132, 0.2)' : 'rgba(234, 57, 67, 0.2)'}`
                              }}>
                                {isProfit ? '+' : ''}{pnlPct?.toFixed(2)}%
                              </Typography>
                            </Box>
                          )}
                        </Box>
                      </TableCell>
                      {/* Col 5: Actions */}
                      <TableCell align="center" sx={{ py: 1.5 }}>
                        <Box sx={{ display: 'flex', gap: 1, justifyContent: 'center' }}>
                          <Button
                            variant="contained"
                            color="success"
                            size="small"
                            onClick={() => onQuickTrade(row.etf, "BUY", hkEtfQty)}
                            disabled={actionLoading || !hasClient || !connected}
                            sx={{ minWidth: 50, height: 28, fontSize: '0.72rem', borderRadius: '6px', boxShadow: 'none' }}
                          >
                            BUY
                          </Button>
                          <Button
                            variant="contained"
                            color="error"
                            size="small"
                            onClick={() => onQuickTrade(row.etf, "SELL", hasPosition ? row.owned_qty : hkEtfQty)}
                            disabled={actionLoading || !hasClient || !connected}
                            sx={{ minWidth: 50, height: 28, fontSize: '0.72rem', borderRadius: '6px', boxShadow: 'none' }}
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
        count={etfData.length}
        rowsPerPage={rowsPerPageEtf}
        page={pageEtf}
        onPageChange={(_, newPage) => setPageEtf(newPage)}
        onRowsPerPageChange={(e) => {
          setPageEtf(0);
          setRowsPerPageEtf(parseInt(e.target.value, 10));
        }}
        sx={{
          borderTop: '1px solid rgba(255, 255, 255, 0.05)',
          color: 'text.secondary',
          '.MuiTablePagination-selectIcon': {
            color: 'text.secondary'
          }
        }}
      />
    </>
  );
});

InverseEtfsTab.displayName = 'InverseEtfsTab';
