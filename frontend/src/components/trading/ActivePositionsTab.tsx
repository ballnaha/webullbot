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
  TablePagination
} from '@mui/material';
import { Position } from './types';

interface ActivePositionsTabProps {
  market: 'US' | 'HK';
  positions: Position[];
  onQuickTrade: (symbol: string, action: 'BUY' | 'SELL', defaultQty?: number) => void | Promise<void>;
  actionLoading: boolean;
  connected: boolean;
  hasClient: boolean;
  stockNames: Record<string, string>;
}

export const ActivePositionsTab: React.FC<ActivePositionsTabProps> = React.memo(({
  market,
  positions,
  onQuickTrade,
  actionLoading,
  connected,
  hasClient,
  stockNames
}) => {
  const [pagePos, setPagePos] = useState(0);
  const [rowsPerPagePos, setRowsPerPagePos] = useState(10);

  const currencyPrefix = market === 'HK' ? 'HK$ ' : '$';

  const isInverseEtf = (symbol: string) => {
    return ["7500.HK", "7552.HK", "SH", "PSQ", "DOG", "SQQQ", "QID", "SDS"].includes(symbol);
  };

  const filteredPositions = positions.filter(pos =>
    market === 'HK' ? pos.symbol.endsWith('.HK') : !pos.symbol.endsWith('.HK')
  );

  return (
    <>
      {/* Market Hour Info Alert */}
      <Box sx={{
        mx: 3,
        my: 2,
        p: 1.5,
        bgcolor: 'rgba(59, 130, 246, 0.04)',
        border: '1px solid rgba(59, 130, 246, 0.15)',
        borderRadius: '8px',
        display: 'flex',
        flexDirection: 'column',
        gap: 0.5
      }}>
        <Typography variant="caption" sx={{ color: 'primary.main', fontWeight: 700, display: 'flex', alignItems: 'center', gap: 1 }}>
          💡 ข้อมูลเวลาเปิด-ปิดตลาด (เวลาประเทศไทย - ICT):
        </Typography>
        {market === 'HK' ? (
          <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.75rem', lineHeight: 1.4 }}>
            🇹🇭 <strong>ตลาดหุ้นฮ่องกง (HKEX):</strong> เปิด <strong>08:30 - 15:00 น.</strong> (พักเที่ยงเวลา 11:00 - 12:00 น.)

          </Typography>
        ) : (
          <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.75rem', lineHeight: 1.4 }}>
            🇹🇭 <strong>ตลาดหุ้นสหรัฐฯ (NYSE/NASDAQ):</strong>
            <br />
            • ⏳ ช่วงเวลาปกติ (Winter Time): <strong>21:30 - 04:00 น.</strong>
            <br />
            • ☀️ ช่วงเวลาออมแสง (Daylight Saving/Summer Time): <strong>20:30 - 03:00 น.</strong>

          </Typography>
        )}
      </Box>
      <TableContainer>
        <Table size="small">
          <TableHead sx={{ bgcolor: 'rgba(255,255,255,0.02)' }}>
            <TableRow>
              <TableCell sx={{ fontWeight: 700, color: '#94a3b8', borderBottom: '1px solid rgba(255,255,255,0.08)', py: 1.5, fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>หุ้น (Ticker)</TableCell>
              <TableCell align="right" sx={{ fontWeight: 700, color: '#94a3b8', borderBottom: '1px solid rgba(255,255,255,0.08)', py: 1.5, fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>จำนวนหุ้น (Shares)</TableCell>
              <TableCell align="right" sx={{ fontWeight: 700, color: '#94a3b8', borderBottom: '1px solid rgba(255,255,255,0.08)', py: 1.5, fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>ทุนเฉลี่ย (Avg Price)</TableCell>
              <TableCell align="right" sx={{ fontWeight: 700, color: '#94a3b8', borderBottom: '1px solid rgba(255,255,255,0.08)', py: 1.5, fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>มูลค่าตลาด (Market Value)</TableCell>
              <TableCell align="right" sx={{ fontWeight: 700, color: '#94a3b8', borderBottom: '1px solid rgba(255,255,255,0.08)', py: 1.5, fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>กำไร / ขาดทุน (P&L)</TableCell>
              <TableCell align="center" sx={{ fontWeight: 700, color: '#94a3b8', borderBottom: '1px solid rgba(255,255,255,0.08)', py: 1.5, fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>แอ็กชัน (Action)</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredPositions.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} align="center" sx={{ py: 8, color: 'text.secondary' }}>
                  ไม่มีหุ้นถือครองอยู่ในพอร์ตโฟลิโอสำหรับตลาดนี้ขณะนี้
                </TableCell>
              </TableRow>
            ) : (
              filteredPositions
                .slice(pagePos * rowsPerPagePos, pagePos * rowsPerPagePos + rowsPerPagePos)
                .map((pos) => {
                  const posProfit = pos.unrealized_pnl >= 0;
                  const isHedge = isInverseEtf(pos.symbol);
                  return (
                    <TableRow key={pos.symbol} hover sx={{ '&:hover': { bgcolor: 'rgba(255,255,255,0.02)' } }}>
                      <TableCell sx={{ py: 1.5 }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Typography sx={{ fontWeight: 800, color: isHedge ? 'secondary.main' : 'primary.main', fontSize: '0.9rem', lineHeight: 1.1 }}>
                            {pos.symbol}
                          </Typography>
                          <Chip
                            label={isHedge ? "SHORT / HEDGE" : "LONG"}
                            size="small"
                            variant="outlined"
                            color={isHedge ? "secondary" : "primary"}
                            sx={{
                              fontSize: '0.62rem',
                              height: 16,
                              fontWeight: 700,
                              borderRadius: '4px',
                              borderColor: isHedge ? 'rgba(99, 102, 241, 0.4)' : 'rgba(59, 130, 246, 0.4)',
                              color: isHedge ? '#a5b4fc' : '#93c5fd'
                            }}
                          />
                        </Box>
                        <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.72rem', display: 'block', mt: 0.2 }}>
                          {stockNames[pos.symbol] || (isHedge ? "Inverse Hedge ETF" : `${market === 'HK' ? 'Hong Kong' : 'US'} Listed Company`)}
                        </Typography>
                      </TableCell>
                      <TableCell align="right" sx={{ fontFamily: 'var(--font-mono)', fontWeight: 600 }}>{pos.qty}</TableCell>
                      <TableCell align="right" sx={{ fontFamily: 'var(--font-mono)', fontWeight: 600 }}>{currencyPrefix}{pos.avg_price.toFixed(2)}</TableCell>
                      <TableCell align="right" sx={{ fontFamily: 'var(--font-mono)', fontWeight: 600 }}>{currencyPrefix}{pos.market_value.toFixed(2)}</TableCell>
                      <TableCell align="right">
                        <Box sx={{ display: "flex", justifyContent: "flex-end", alignItems: "center", gap: 1 }}>
                          <Typography
                            sx={{
                              color: posProfit ? 'success.main' : 'error.main',
                              fontWeight: 700,
                              fontFamily: 'var(--font-mono)'
                            }}
                          >
                            {posProfit ? "+" : ""}{currencyPrefix}{pos.unrealized_pnl.toFixed(2)}
                          </Typography>
                          <Chip
                            label={pos.avg_price > 0 ? `${posProfit ? "+" : ""}${(pos.unrealized_pnl / (pos.avg_price * pos.qty) * 100).toFixed(2)}%` : "0.00%"}
                            size="small"
                            color={posProfit ? "success" : "error"}
                            sx={{
                              fontWeight: 800,
                              fontSize: '0.7rem',
                              height: 18,
                              borderRadius: '4px',
                              px: 0.5,
                              minWidth: 55,
                              textAlign: 'right'
                            }}
                          />
                        </Box>
                      </TableCell>
                      <TableCell align="center" sx={{ py: 1.5 }}>
                        <Button
                          variant="contained"
                          color="error"
                          size="small"
                          onClick={() => onQuickTrade(pos.symbol, "SELL", pos.qty)}
                          disabled={actionLoading || !hasClient || !connected}
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

      {filteredPositions.length > 0 && (
        <TablePagination
          rowsPerPageOptions={[5, 10, 20, 50, 100]}
          component="div"
          count={filteredPositions.length}
          rowsPerPage={rowsPerPagePos}
          page={pagePos}
          onPageChange={(_, newPage) => setPagePos(newPage)}
          onRowsPerPageChange={(e) => {
            setRowsPerPagePos(parseInt(e.target.value, 10));
            setPagePos(0);
          }}
          sx={{
            borderTop: '1px solid rgba(255, 255, 255, 0.05)',
            color: 'text.secondary',
            '.MuiTablePagination-selectIcon': {
              color: 'text.secondary'
            }
          }}
        />
      )}
    </>
  );
});

ActivePositionsTab.displayName = 'ActivePositionsTab';
