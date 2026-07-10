import React, { useState, useMemo } from 'react';
import { 
  Table, 
  TableBody, 
  TableCell, 
  TableContainer, 
  TableHead, 
  TableRow,
  Typography,
  Box,
  Chip,
  TablePagination
} from '@mui/material';
import { TrendingUp, Clock } from 'lucide-react';
import {
  ResponsiveContainer,
  ComposedChart,
  Line,
  Bar,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ReferenceLine
} from 'recharts';
import { Trade } from './types';

interface TradeHistoryTabProps {
  market: 'US' | 'HK';
  trades: Trade[];
  stockNames: Record<string, string>;
}

export const TradeHistoryTab: React.FC<TradeHistoryTabProps> = React.memo(({
  market,
  trades,
  stockNames
}) => {
  const [pageHistory, setPageHistory] = useState(0);
  const [rowsPerPageHistory, setRowsPerPageHistory] = useState(10);

  const currencyPrefix = market === 'HK' ? 'HK$ ' : '$';

  // 1. Calculate Cost Basis and Realized PnL chronologically (oldest first)
  const decoratedTrades = useMemo(() => {
    const sorted = [...trades].sort((a, b) => {
      const timeA = a.time || a.timestamp || "";
      const timeB = b.time || b.timestamp || "";
      return timeA.localeCompare(timeB);
    });

    const holdings: Record<string, { qty: number; totalCost: number }> = {};
    
    return sorted.map(trade => {
      const symbol = trade.symbol;
      const qty = trade.qty || 0;
      const price = trade.price || 0;
      const action = (trade.action || "BUY").toUpperCase();
      
      let avgBuyPrice = 0;
      let realizedPnL = 0;
      let pnlPct = 0;

      if (action.startsWith("BUY")) {
        if (!holdings[symbol]) {
          holdings[symbol] = { qty: 0, totalCost: 0 };
        }
        holdings[symbol].qty += qty;
        holdings[symbol].totalCost += qty * price;
        avgBuyPrice = price;
      } else if (action.startsWith("SELL")) {
        const state = holdings[symbol];
        if (state && state.qty > 0) {
          avgBuyPrice = state.totalCost / state.qty;
          realizedPnL = (price - avgBuyPrice) * qty;
          pnlPct = ((price - avgBuyPrice) / avgBuyPrice) * 100;
          
          state.qty = Math.max(0, state.qty - qty);
          state.totalCost = state.qty * avgBuyPrice;
        }
      }
      
      return {
        ...trade,
        avgBuyPrice,
        realizedPnL,
        pnlPct
      };
    });
  }, [trades]);

  // 2. Filter trades by market & Process chart data + metrics
  const { chartData, totalSells, winRate, cumulativePnL, filteredTrades } = useMemo(() => {
    let cumulative = 0;
    let sellsCount = 0;
    let winsCount = 0;

    // Filter by market
    const filtered = decoratedTrades.filter(trade => 
      market === 'HK' ? trade.symbol.endsWith('.HK') : !trade.symbol.endsWith('.HK')
    );

    const mapped = filtered.map((trade, idx) => {
      const isBuy = trade.action.toUpperCase().startsWith("BUY");
      const pnl = trade.realizedPnL || 0;
      
      if (!isBuy) {
        sellsCount += 1;
        cumulative += pnl;
        if (pnl > 0) {
          winsCount += 1;
        }
      }
      
      const timeVal = trade.time || trade.timestamp || "N/A";
      const timePart = timeVal.includes(" ") ? timeVal.split(" ")[1] : timeVal;
      
      return {
        tradeIndex: idx + 1,
        label: `${timePart} (${trade.symbol})`,
        symbol: trade.symbol,
        action: trade.action,
        qty: trade.qty,
        price: trade.price,
        pnl: isBuy ? 0 : Number(pnl.toFixed(2)),
        cumulative: Number(cumulative.toFixed(2)),
      };
    });

    const rate = sellsCount > 0 ? (winsCount / sellsCount) * 100 : 0;

    return {
      chartData: mapped,
      totalSells: sellsCount,
      winRate: Number(rate.toFixed(1)),
      cumulativePnL: Number(cumulative.toFixed(2)),
      filteredTrades: filtered
    };
  }, [decoratedTrades, market]);

  return (
    <>
      {/* Trading Performance Analytics Chart */}
      <Box sx={{ mb: 4, px: market === 'US' ? 3 : 0, pt: market === 'US' ? 3 : 0 }}>
        <Box sx={{ display: "flex", flexDirection: { xs: 'column', md: 'row' }, alignItems: { xs: 'flex-start', md: 'center' }, justifyContent: 'space-between', gap: 2, mb: 3 }}>
          <Box sx={{ display: 'flex', alignItems: "center", gap: 1.5, flexGrow: 1 }}>
            <Box sx={{ p: 1, borderRadius: '10px', bgcolor: 'rgba(99, 102, 241, 0.08)', display: 'flex' }}>
              <TrendingUp size={20} color="#6366f1" />
            </Box>
            <Box>
              <Typography variant="h6" sx={{ fontWeight: 800 }}>
                วิเคราะห์ผลการเทรด & เส้นอัตรากำไร (Performance Analytics & Equity Curve)
              </Typography>
              <Typography variant="caption" color="text.secondary">
                กำไร/ขาดทุนรายดีล{market === 'HK' ? 'ฮ่องกง' : 'สหรัฐฯ'} (แท่ง) ซ้อนทับกับ กำไรสะสมสุทธิ (เส้น)
              </Typography>
            </Box>
          </Box>
          
          {/* Metrics Summary Panel */}
          <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', width: { xs: '100%', md: 'auto' } }}>
            <Box sx={{ px: 2, py: 1, bgcolor: 'rgba(255,255,255,0.02)', borderRadius: '10px', border: '1px solid rgba(148, 163, 184, 0.06)' }}>
              <Typography variant="caption" color="text.secondary" sx={{ display: 'block', fontWeight: 600 }}>ดีลที่ปิดธุรกรรม (Sells)</Typography>
              <Typography variant="body1" sx={{ fontWeight: 800, fontFamily: 'var(--font-mono)' }}>{totalSells} ครั้ง</Typography>
            </Box>
            <Box sx={{ px: 2, py: 1, bgcolor: 'rgba(255,255,255,0.02)', borderRadius: '10px', border: '1px solid rgba(148, 163, 184, 0.06)' }}>
              <Typography variant="caption" color="text.secondary" sx={{ display: 'block', fontWeight: 600 }}>อัตราการชนะ (Win Rate)</Typography>
              <Typography variant="body1" sx={{ fontWeight: 800, color: winRate >= 50 ? 'success.main' : 'warning.main', fontFamily: 'var(--font-mono)' }}>{winRate}%</Typography>
            </Box>
            <Box sx={{ px: 2, py: 1, bgcolor: 'rgba(255,255,255,0.02)', borderRadius: '10px', border: '1px solid rgba(148, 163, 184, 0.06)' }}>
              <Typography variant="caption" color="text.secondary" sx={{ display: 'block', fontWeight: 600 }}>กำไรสะสมสุทธิ (Net Return)</Typography>
              <Typography variant="body1" sx={{ fontWeight: 800, color: cumulativePnL >= 0 ? 'success.main' : 'error.main', fontFamily: 'var(--font-mono)' }}>
                {cumulativePnL >= 0 ? '+' : ''}{currencyPrefix}{cumulativePnL.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </Typography>
            </Box>
          </Box>
        </Box>

        {chartData.length === 0 ? (
          <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: 200, bgcolor: 'rgba(0,0,0,0.15)', borderRadius: '12px', border: '1px dashed rgba(255,255,255,0.06)', p: 3 }}>
            <TrendingUp size={40} color="#94a3b8" style={{ opacity: 0.3, marginBottom: 12 }} />
            <Typography variant="body2" color="text.secondary">ไม่มีข้อมูลธุรกรรมซื้อขาย{market === 'HK' ? 'ฮ่องกง' : 'สหรัฐฯ'} ที่จะแสดงผลกราฟในขณะนี้</Typography>
          </Box>
        ) : (
          <Box sx={{ width: '100%', height: 300, mt: 1, p: 2, bgcolor: 'rgba(255,255,255,0.01)', borderRadius: '12px', border: '1px solid rgba(148, 163, 184, 0.04)' }}>
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart
                data={chartData}
                margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(148, 163, 184, 0.06)" />
                <XAxis 
                  dataKey="label" 
                  stroke="#64748b" 
                  fontSize={10}
                  tickLine={false}
                  axisLine={false}
                  dy={10}
                />
                <YAxis 
                  stroke="#64748b" 
                  fontSize={10}
                  tickLine={false}
                  axisLine={false}
                  tickFormatter={(value) => `${value >= 0 ? '+' : ''}${value}`}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#0f141c',
                    borderColor: 'rgba(148, 163, 184, 0.12)',
                    borderRadius: '12px',
                    boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.5)',
                  }}
                  labelStyle={{ fontWeight: 800, color: '#3b82f6', marginBottom: 6, fontSize: '0.85rem' }}
                  itemStyle={{ fontSize: '0.85rem' }}
                  formatter={(value: any, name: any, props: any) => {
                    const valNum = Number(value);
                    const formattedVal = `${valNum >= 0 ? '+' : ''}${currencyPrefix}${valNum.toFixed(2)}`;
                    if (name === 'pnl') return [formattedVal, 'กำไร/ขาดทุนดีลนี้ (PnL)'];
                    if (name === 'cumulative') return [formattedVal, 'กำไรสะสมสุทธิ (Total Return)'];
                    return [value, name];
                  }}
                  labelFormatter={(label, items) => {
                    if (items && items[0]) {
                      const p = items[0].payload;
                      return `${p.action} ${p.qty} หุ้น ${p.symbol} @ ${currencyPrefix}${p.price.toFixed(2)}`;
                    }
                    return label;
                  }}
                />
                <Legend 
                  verticalAlign="top" 
                  height={36} 
                  iconType="circle"
                  iconSize={8}
                  wrapperStyle={{ fontSize: '0.75rem', color: '#94a3b8' }}
                />
                <ReferenceLine y={0} stroke="rgba(148, 163, 184, 0.2)" strokeWidth={1} />
                <Bar 
                  dataKey="pnl" 
                  name="กำไร/ขาดทุนรายดีล (Trade PnL)"
                  barSize={20}
                  radius={[4, 4, 0, 0]}
                >
                  {chartData.map((entry, index) => (
                    <Cell 
                      key={`cell-${index}`} 
                      fill={entry.pnl >= 0 ? '#16c784' : '#ea3943'} 
                      fillOpacity={entry.pnl === 0 ? 0.05 : 0.8}
                    />
                  ))}
                </Bar>
                <Line 
                  type="monotone" 
                  dataKey="cumulative" 
                  name="กำไรสะสมรวม (Cumulative PnL)" 
                  stroke="#6366f1" 
                  strokeWidth={3}
                  dot={{ r: 4, strokeWidth: 1, fill: '#0a0e1a' }}
                  activeDot={{ r: 6, strokeWidth: 0 }}
                />
              </ComposedChart>
            </ResponsiveContainer>
          </Box>
        )}
      </Box>

      {/* Trade History Table */}
      <TableContainer sx={{ px: market === 'US' ? 3 : 0 }}>
        <Table size="small">
          <TableHead sx={{ bgcolor: 'rgba(255,255,255,0.02)' }}>
            <TableRow>
              <TableCell sx={{ fontWeight: 700, color: '#94a3b8', borderBottom: '1px solid rgba(255,255,255,0.08)', py: 1.5, fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em', pl: 3 }}>เวลาทำรายการ (Time)</TableCell>
              <TableCell sx={{ fontWeight: 700, color: '#94a3b8', borderBottom: '1px solid rgba(255,255,255,0.08)', py: 1.5, fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>หุ้น (Ticker)</TableCell>
              <TableCell align="center" sx={{ fontWeight: 700, color: '#94a3b8', borderBottom: '1px solid rgba(255,255,255,0.08)', py: 1.5, fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>ประเภทคำสั่ง</TableCell>
              <TableCell align="right" sx={{ fontWeight: 700, color: '#94a3b8', borderBottom: '1px solid rgba(255,255,255,0.08)', py: 1.5, fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>จำนวนหุ้น (Qty)</TableCell>
              <TableCell align="right" sx={{ fontWeight: 700, color: '#94a3b8', borderBottom: '1px solid rgba(255,255,255,0.08)', py: 1.5, fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>ราคาทำรายการ (Price)</TableCell>
              <TableCell align="right" sx={{ fontWeight: 700, color: '#94a3b8', borderBottom: '1px solid rgba(255,255,255,0.08)', py: 1.5, fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>ต้นทุนเฉลี่ย (Cost Basis)</TableCell>
              <TableCell align="right" sx={{ fontWeight: 700, color: '#94a3b8', borderBottom: '1px solid rgba(255,255,255,0.08)', py: 1.5, fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>ราคารวม (Total)</TableCell>
              <TableCell align="right" sx={{ fontWeight: 700, color: '#94a3b8', borderBottom: '1px solid rgba(255,255,255,0.08)', py: 1.5, fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>กำไร / ขาดทุน (PnL)</TableCell>
              <TableCell align="center" sx={{ fontWeight: 700, color: '#94a3b8', borderBottom: '1px solid rgba(255,255,255,0.08)', py: 1.5, fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>สถานะออเดอร์</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredTrades.length === 0 ? (
              <TableRow>
                <TableCell colSpan={9} align="center" sx={{ py: 8, color: 'text.secondary' }}>
                  ไม่มีประวัติธุรกรรมซื้อขายหลักทรัพย์{market === 'HK' ? 'ฮ่องกง' : 'สหรัฐฯ'} ในขณะนี้
                </TableCell>
              </TableRow>
            ) : (
              [...filteredTrades]
                .reverse()
                .slice(pageHistory * rowsPerPageHistory, pageHistory * rowsPerPageHistory + rowsPerPageHistory)
                .map((trade, idx) => {
                  const isBuy = trade.action.toUpperCase().startsWith("BUY");
                  const time = trade.time || trade.timestamp || "N/A";
                  const status = trade.status || "FILLED";
                  const price = trade.price || 0;
                  const qty = trade.qty || 0;
                  const total = trade.total || (qty * price);
                  const costBasis = trade.avgBuyPrice || 0;
                  const pnl = trade.realizedPnL || 0;
                  const pnlPct = trade.pnlPct || 0;
                  const pnlPositive = pnl >= 0;
                  
                  return (
                    <TableRow key={idx} hover sx={{ '&:hover': { bgcolor: 'rgba(255,255,255,0.02)' } }}>
                      <TableCell sx={{ py: 1.5, color: 'text.secondary', fontSize: '0.85rem', pl: 3 }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Clock size={12} /> {time}
                        </Box>
                      </TableCell>
                      <TableCell sx={{ py: 1.5 }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Typography sx={{ fontWeight: 800, color: 'primary.main', fontSize: '0.9rem', lineHeight: 1.1 }}>
                            {trade.symbol}
                          </Typography>
                        </Box>
                        <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.72rem', display: 'block', mt: 0.2 }}>
                           {stockNames[trade.symbol] || `${market === 'HK' ? 'Hong Kong' : 'US'} Listed Company`}
                        </Typography>
                      </TableCell>
                      <TableCell align="center" sx={{ py: 1.5 }}>
                        <Chip 
                          label={trade.action}
                          size="small"
                          color={isBuy ? "success" : "error"}
                          sx={{ fontWeight: 800, fontSize: '0.7rem', height: 20, borderRadius: '6px' }}
                        />
                      </TableCell>
                      <TableCell align="right" sx={{ py: 1.5, fontFamily: 'var(--font-mono)', fontWeight: 600 }}>{qty}</TableCell>
                      <TableCell align="right" sx={{ py: 1.5, fontFamily: 'var(--font-mono)', fontWeight: 600 }}>{currencyPrefix}{price.toFixed(2)}</TableCell>
                      <TableCell align="right" sx={{ py: 1.5, fontFamily: 'var(--font-mono)', fontWeight: 600 }}>
                        {costBasis > 0 ? `${currencyPrefix}${costBasis.toFixed(2)}` : "-"}
                      </TableCell>
                      <TableCell align="right" sx={{ py: 1.5, fontFamily: 'var(--font-mono)', fontWeight: 600 }}>{currencyPrefix}{total.toFixed(2)}</TableCell>
                      <TableCell align="right" sx={{ py: 1.5 }}>
                        {!isBuy && costBasis > 0 ? (
                          <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end' }}>
                            <Typography sx={{ color: pnlPositive ? 'success.main' : 'error.main', fontWeight: 700, fontFamily: 'var(--font-mono)', fontSize: '0.9rem' }}>
                              {pnlPositive ? '+' : ''}{currencyPrefix}{pnl.toFixed(2)}
                            </Typography>
                            <Typography variant="caption" sx={{ color: pnlPositive ? 'success.main' : 'error.main', fontWeight: 700, fontSize: '0.72rem' }}>
                              {pnlPositive ? '+' : ''}{pnlPct.toFixed(2)}%
                            </Typography>
                          </Box>
                        ) : (
                          <Typography color="text.secondary" sx={{ fontSize: '0.9rem' }}>-</Typography>
                        )}
                      </TableCell>
                      <TableCell align="center" sx={{ py: 1.5 }}>
                        <Typography variant="body2" sx={{ fontWeight: 700, color: status.toLowerCase() === "filled" ? 'success.main' : 'text.secondary' }}>
                          {status.toUpperCase()}
                        </Typography>
                      </TableCell>
                    </TableRow>
                  );
                })
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {filteredTrades.length > 0 && (
        <Box sx={{ px: market === 'US' ? 3 : 0 }}>
          <TablePagination
            rowsPerPageOptions={[5, 10, 20, 50, 100]}
            component="div"
            count={filteredTrades.length}
            rowsPerPage={rowsPerPageHistory}
            page={pageHistory}
            onPageChange={(_, newPage) => setPageHistory(newPage)}
            onRowsPerPageChange={(e) => {
              setRowsPerPageHistory(parseInt(e.target.value, 10));
              setPageHistory(0);
            }}
            sx={{
              borderTop: '1px solid rgba(255, 255, 255, 0.05)',
              color: 'text.secondary',
              '.MuiTablePagination-selectIcon': {
                color: 'text.secondary'
              }
            }}
          />
        </Box>
      )}
    </>
  );
});

TradeHistoryTab.displayName = 'TradeHistoryTab';
