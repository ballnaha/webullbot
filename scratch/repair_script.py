with open('frontend/src/app/logs/page.tsx', 'rb') as f:
    data = f.read()

marker = b'History size={20} color="#6366f1" />\n                </Box>\n                <Box>\n                  <Typography variant="h6" sx={{ fontWeight: 800 }}>\n'
pos = data.find(marker)
if pos == -1:
    print("Error: Marker not found")
    exit(1)

new_content_str = """                    ประวัติรายการส่งคำสั่งซื้อขาย (Order Transmission History)
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
                      <TableCell align="right">ต้นทุนเฉลี่ย (Cost Basis)</TableCell>
                      <TableCell align="right">ราคารวม (Total)</TableCell>
                      <TableCell align="right">กำไร / ขาดทุน (PnL)</TableCell>
                      <TableCell align="center">สถานะออเดอร์</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {trades.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={9} align="center" sx={{ py: 6, color: 'text.secondary' }}>
                          ไม่มีประวัติออเดอร์การซื้อขายในระบบในขณะนี้
                        </TableCell>
                      </TableRow>
                    ) : (
                      [...decoratedTrades].reverse().map((trade, idx) => {
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
                        const curPrefix = trade.symbol.endsWith(".HK") ? "HK$ " : "$";
                        return (
                          <TableRow key={idx} hover sx={{ '&:hover': { bgcolor: 'rgba(255,255,255,0.02)' } }}>
                            <TableCell sx={{ py: 1.5, display: 'flex', alignItems: 'center', gap: 1, color: 'text.secondary', fontSize: '0.85rem' }}>
                              <Clock size={12} /> {time}
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
                            <TableCell align="right" sx={{ py: 1.5, fontFamily: 'var(--font-mono)' }}>{curPrefix}{price.toFixed(2)}</TableCell>
                            <TableCell align="right" sx={{ py: 1.5, fontFamily: 'var(--font-mono)' }}>
                              {costBasis > 0 ? `${curPrefix}${costBasis.toFixed(2)}` : "-"}
                            </TableCell>
                            <TableCell align="right" sx={{ py: 1.5, fontFamily: 'var(--font-mono)' }}>{curPrefix}{total.toFixed(2)}</TableCell>
                            <TableCell align="right" sx={{ py: 1.5 }}>
                              {!isBuy && costBasis > 0 ? (
                                <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end' }}>
                                  <Typography sx={{ color: pnlPositive ? 'success.main' : 'error.main', fontWeight: 700, fontFamily: 'var(--font-mono)', fontSize: '0.9rem' }}>
                                    {pnlPositive ? '+' : ''}{curPrefix}{pnl.toFixed(2)}
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
            </CardContent>
          </Card>

        </Box>
    </>
  );
}
"""

new_data = data[:pos + len(marker)] + new_content_str.encode('utf-8')
with open('frontend/src/app/logs/page.tsx', 'wb') as f:
    f.write(new_data)
print("File successfully repaired!")
