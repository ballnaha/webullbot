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

interface LongScannerTabProps {
  market: 'US' | 'HK';
  filteredSignals: SignalData[];
  signals: SignalData[];
  onQuickTrade: (symbol: string, action: 'BUY' | 'SELL', defaultQty?: number) => void | Promise<void>;
  actionLoading: boolean;
  connected: boolean;
  isSignalsLoading: boolean;
  hasClient: boolean;
  maxPrice: string;
  priceOperator: 'le' | 'ge';
  stockNames: Record<string, string>;
}

export const LongScannerTab: React.FC<LongScannerTabProps> = React.memo(({
  market,
  filteredSignals,
  signals,
  onQuickTrade,
  actionLoading,
  connected,
  isSignalsLoading,
  hasClient,
  maxPrice,
  priceOperator,
  stockNames
}) => {
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);

  const currencyPrefix = market === 'HK' ? 'HK$ ' : '$';

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

  return (
    <>
      <Box sx={{ px: 3, pb: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 1 }}>
        <Typography variant="caption" sx={{ color: 'text.secondary', fontWeight: 500 }}>
          📊 กำลังแสดง <span style={{ color: '#3b82f6', fontWeight: 700 }}>{filteredSignals.length}</span> จากทั้งหมด <span style={{ fontWeight: 600 }}>{signals.filter(s => market === 'HK' ? s.symbol.endsWith('.HK') : !s.symbol.endsWith('.HK')).length}</span> หุ้น{market === 'HK' ? 'ฮ่องกง' : 'สหรัฐฯ'}ในระบบสแกนเนอร์
        </Typography>
        {maxPrice && (
          <Typography variant="caption" sx={{ color: 'success.main', fontWeight: 600, bgcolor: 'rgba(16, 185, 129, 0.08)', px: 1.5, py: 0.4, borderRadius: '6px', border: '1px solid rgba(16, 185, 129, 0.15)' }}>
            คัดกรอง: ราคา {priceOperator === 'ge' ? '≥' : '≤'} {maxPrice} {market === 'HK' ? 'HKD' : 'USD'}
          </Typography>
        )}
      </Box>

      <TableContainer>
        <Table size="small">
          <TableHead sx={{ bgcolor: 'rgba(255,255,255,0.02)' }}>
            <TableRow>
              <TableCell sx={{ fontWeight: 700, color: '#94a3b8', borderBottom: '1px solid rgba(255,255,255,0.08)', py: 1.5, fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em', width: '28%' }}>หุ้น / บริษัท (Ticker & Company)</TableCell>
              <TableCell align="right" sx={{ fontWeight: 700, color: '#94a3b8', borderBottom: '1px solid rgba(255,255,255,0.08)', py: 1.5, fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em', width: '12%' }}>ราคาล่าสุด</TableCell>
              <TableCell align="left" sx={{ pl: 4, fontWeight: 700, color: '#94a3b8', borderBottom: '1px solid rgba(255,255,255,0.08)', py: 1.5, fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em', width: '25%' }}>ตัวชี้วัดทางเทคนิค (Technical Indicators)</TableCell>
              <TableCell align="center" sx={{ fontWeight: 700, color: '#94a3b8', borderBottom: '1px solid rgba(255,255,255,0.08)', py: 1.5, fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em', width: '20%' }}>ความสอดคล้องสัญญาณ (Confluence)</TableCell>
              <TableCell align="center" sx={{ fontWeight: 700, color: '#94a3b8', borderBottom: '1px solid rgba(255,255,255,0.08)', py: 1.5, fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em', width: '15%' }}>ซื้อขายด่วน (Quick Trade)</TableCell>
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
                  const conf = getConfluenceSignal(sig.sma_signal, sig.rsi_signal, sig.hybrid_signal);
                  return (
                    <TableRow key={sig.symbol} hover sx={{ '&:hover': { bgcolor: 'rgba(255,255,255,0.02)' } }}>
                      <TableCell sx={{ py: 1.5 }}>
                        <Typography sx={{ fontWeight: 800, color: 'primary.main', fontSize: '0.9rem', lineHeight: 1.1 }}>
                          {sig.symbol}
                        </Typography>
                        <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.72rem', display: 'block', mt: 0.2 }}>
                          {stockNames[sig.symbol] || (sig.symbol.endsWith('.HK') ? "Hong Kong Listed Company" : "US Listed Company")}
                        </Typography>
                      </TableCell>
                      <TableCell align="right" sx={{ fontFamily: 'var(--font-mono)', fontWeight: 600, py: 1.5 }}>
                        {sig.price > 0 ? `${currencyPrefix} ${sig.price.toFixed(2)}` : "N/A"}
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
                            SMA(10/30): {sig.sma_fast > 0 ? `${currencyPrefix} ${sig.sma_fast.toFixed(2)} / ${currencyPrefix} ${sig.sma_slow.toFixed(2)}` : "N/A"}
                          </Typography>
                          {sig.volume_ema_signal && (
                            <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.75rem', display: 'block', mt: 0.1 }}>
                              Volume+EMA (9/21): <span style={{ 
                                color: sig.volume_ema_signal === "BUY" ? '#16c784' : sig.volume_ema_signal === "SELL" ? '#ea3943' : '#94a3b8',
                                fontWeight: sig.volume_ema_signal !== "HOLD" ? 700 : 500
                              }}>{sig.volume_ema_signal}</span>
                            </Typography>
                          )}
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
                            onClick={() => onQuickTrade(sig.symbol, "BUY")}
                            disabled={actionLoading || !hasClient || !connected}
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
                            onClick={() => onQuickTrade(sig.symbol, "SELL")}
                            disabled={actionLoading || !hasClient || !connected}
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
    </>
  );
});

LongScannerTab.displayName = 'LongScannerTab';
