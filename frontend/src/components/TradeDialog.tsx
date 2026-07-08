"use client";

import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Typography,
  Button,
  Box,
  TextField,
  CircularProgress,
  IconButton,
  Zoom,
  InputAdornment
} from '@mui/material';
import { TransitionProps } from '@mui/material/transitions';
import { TrendingUp, TrendingDown, X, DollarSign, Minus, Plus } from 'lucide-react';

const Transition = React.forwardRef(function Transition(
  props: TransitionProps & {
    children: React.ReactElement<any, any>;
  },
  ref: React.Ref<unknown>,
) {
  return <Zoom ref={ref} {...props} />;
});

interface TradeDialogProps {
  open: boolean;
  symbol: string;
  action: 'BUY' | 'SELL';
  defaultQty: number;
  onConfirm: (qty: number) => void;
  onCancel: () => void;
  loading?: boolean;
  /** 'shares' = quantity in shares (HK), 'cash' = quantity in USD budget (US) */
  mode?: 'shares' | 'cash';
}

export default function TradeDialog({
  open,
  symbol,
  action,
  defaultQty,
  onConfirm,
  onCancel,
  loading = false,
  mode = 'shares'
}: TradeDialogProps) {
  const [qty, setQty] = useState<string>(defaultQty.toString());
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (open) {
      setQty(defaultQty.toString());
      setError(null);
    }
  }, [open, defaultQty]);

  const handleSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const qtyNum = parseFloat(qty);
    if (isNaN(qtyNum) || qtyNum <= 0) {
      setError(mode === 'cash' ? 'กรุณาระบุจำนวนเงินที่มากกว่า $0' : 'กรุณาระบุจำนวนหุ้นที่มากกว่า 0');
      return;
    }
    setError(null);
    onConfirm(qtyNum);
  };

  const isBuy = action === 'BUY';
  const isCash = mode === 'cash';
  const actionColor = isBuy ? '#16c784' : '#ea3943'; // Green for BUY, Red for SELL
  const actionGradient = isBuy 
    ? 'linear-gradient(135deg, #16c784, #0fa56c)' 
    : 'linear-gradient(135deg, #ea3943, #d6222b)';

  const quickQtysShares = [1, 5, 10, 50, 100];
  const quickQtysCash = [1, 5, 10, 50, 100];

  const quickQtys = isCash ? quickQtysCash : quickQtysShares;
  const stepSize = 1;

  const inputLabel = isCash
    ? 'ระบุจำนวนเงิน (USD) ที่ต้องการส่งคำสั่ง:'
    : 'ระบุจำนวนหุ้นที่ต้องการส่งคำสั่ง:';

  return (
    <Dialog
      open={open}
      slots={{ transition: Transition }}
      onClose={loading ? undefined : onCancel}
      maxWidth="xs"
      fullWidth
      slotProps={{
        backdrop: {
          sx: {
            backgroundColor: 'rgba(4, 6, 12, 0.85)',
            backdropFilter: 'blur(8px)',
            transition: 'all 0.3s'
          }
        },
        paper: {
          sx: {
            bgcolor: '#0d111a',
            backgroundImage: 'linear-gradient(180deg, #111726 0%, #0d111a 100%)',
            border: '1px solid rgba(148, 163, 184, 0.08)',
            borderRadius: '24px',
            p: 2.5,
            position: 'relative',
            boxShadow: `0 24px 60px -10px rgba(0, 0, 0, 0.85), 0 0 40px ${actionColor}0a`,
            overflow: 'hidden',
            '&::before': {
              content: '""',
              position: 'absolute',
              top: 0,
              left: 0,
              right: 0,
              height: '4px',
              background: actionGradient
            }
          }
        }
      }}
    >
      {/* Close Button */}
      {!loading && (
        <IconButton
          onClick={onCancel}
          sx={{
            position: 'absolute',
            right: 16,
            top: 16,
            color: 'text.secondary',
            transition: 'all 0.2s',
            bgcolor: 'rgba(255, 255, 255, 0.02)',
            border: '1px solid rgba(148, 163, 184, 0.06)',
            '&:hover': {
              color: 'text.primary',
              bgcolor: 'rgba(255, 255, 255, 0.05)',
              transform: 'rotate(90deg)'
            }
          }}
        >
          <X size={16} />
        </IconButton>
      )}

      {/* Title */}
      <DialogTitle component="div" sx={{ p: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 1.5, textAlign: 'center', mt: 1 }}>
        <Box
          sx={{
            width: 56,
            height: 56,
            borderRadius: '16px',
            bgcolor: `${actionColor}12`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            border: `1.5px solid ${actionColor}25`,
            mb: 0.5
          }}
        >
          {isBuy ? (
            <TrendingUp size={26} color={actionColor} />
          ) : (
            <TrendingDown size={26} color={actionColor} />
          )}
        </Box>
        <Typography variant="h6" sx={{ fontWeight: 800, color: '#f8fafc', letterSpacing: '-0.01em' }}>
          ส่งออเดอร์ด่วน (Quick Trade)
        </Typography>
        <Box sx={{ display: 'flex', gap: 1, alignItems: 'center', mt: -0.5 }}>
          <Box 
            sx={{ 
              px: 1.5, 
              py: 0.3, 
              borderRadius: '6px', 
              bgcolor: `${actionColor}15`, 
              color: actionColor,
              fontSize: '0.75rem',
              fontWeight: 800
            }}
          >
            {isBuy ? 'ซื้อ (BUY)' : 'ขาย (SELL)'}
          </Box>
          <Typography variant="subtitle2" sx={{ fontWeight: 800, color: '#f1f5f9' }}>
            {symbol}
          </Typography>
        </Box>
      </DialogTitle>

      {/* Input & Form */}
      <DialogContent sx={{ px: 1, py: 2, mt: 1 }}>
        <Box component="form" onSubmit={handleSubmit} sx={{ display: 'flex', flexDirection: 'column', gap: 2.5 }}>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
            <Typography variant="caption" sx={{ color: '#94a3b8', fontWeight: 700, px: 0.5 }}>
              {inputLabel}
            </Typography>
            <TextField
              type="number"
              fullWidth
              size="medium"
              value={qty}
              onChange={(e) => {
                setQty(e.target.value);
                setError(null);
              }}
              error={!!error}
              helperText={error}
              autoFocus
              slotProps={{
                input: {
                  inputProps: { min: isCash ? 0.01 : 1, step: stepSize, style: { textAlign: 'center' } },
                  startAdornment: (
                    <InputAdornment position="start">
                      <IconButton 
                        size="small" 
                        onClick={() => {
                          const currentVal = parseFloat(qty.toString()) || (isCash ? 1 : 1);
                          const newVal = Math.max(isCash ? 0.01 : 1, currentVal - stepSize);
                          setQty(isCash ? newVal.toString() : Math.floor(newVal).toString());
                          setError(null);
                        }}
                        disabled={loading || (parseFloat(qty.toString()) || 1) <= (isCash ? 0.01 : 1)}
                        sx={{ color: 'text.secondary' }}
                      >
                        <Minus size={16} />
                      </IconButton>
                    </InputAdornment>
                  ),
                  endAdornment: (
                    <InputAdornment position="end">
                      <IconButton 
                        size="small" 
                        onClick={() => {
                          const currentVal = parseFloat(qty.toString()) || (isCash ? 1 : 1);
                          const newVal = currentVal + stepSize;
                          setQty(isCash ? newVal.toString() : Math.floor(newVal).toString());
                          setError(null);
                        }}
                        disabled={loading}
                        sx={{ color: 'text.secondary' }}
                      >
                        <Plus size={16} />
                      </IconButton>
                    </InputAdornment>
                  ),
                  sx: {
                    fontSize: '1.1rem',
                    fontWeight: 700,
                    fontFamily: 'var(--font-mono)'
                  }
                }
              }}
            />
          </Box>

          {/* Quick Select Buttons */}
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
            <Typography variant="caption" sx={{ color: '#94a3b8', fontWeight: 700, px: 0.5 }}>
              ตัวเลือกด่วน:
            </Typography>
            <Box sx={{ display: 'flex', gap: 1 }}>
              {quickQtys.map((q) => (
                <Button
                  key={q}
                  variant="outlined"
                  size="small"
                  onClick={() => {
                    setQty(q.toString());
                    setError(null);
                  }}
                  sx={{
                    flex: 1,
                    py: 0.5,
                    borderRadius: '8px',
                    borderColor: 'rgba(148, 163, 184, 0.1)',
                    color: '#94a3b8',
                    fontWeight: 700,
                    fontSize: '0.78rem',
                    fontFamily: 'var(--font-mono)',
                    '&:hover': {
                      borderColor: actionColor,
                      color: '#f8fafc',
                      bgcolor: `${actionColor}0a`
                    }
                  }}
                >
                  {isCash ? `$${q}` : `+${q}`}
                </Button>
              ))}
            </Box>
          </Box>
        </Box>
      </DialogContent>

      {/* Actions */}
      <DialogActions sx={{ p: 1, display: 'flex', gap: 2, mt: 1 }}>
        <Button
          onClick={onCancel}
          disabled={loading}
          variant="outlined"
          sx={{
            flex: 1,
            height: 44,
            borderRadius: '12px',
            color: '#94a3b8',
            borderColor: 'rgba(148, 163, 184, 0.1)',
            fontSize: '0.88rem',
            fontWeight: 700,
            textTransform: 'none',
            '&:hover': {
              borderColor: 'rgba(148, 163, 184, 0.25)',
              bgcolor: 'rgba(255, 255, 255, 0.03)',
              color: '#f8fafc'
            }
          }}
        >
          ยกเลิก
        </Button>
        <Button
          onClick={() => handleSubmit()}
          disabled={loading}
          variant="contained"
          sx={{
            flex: 1,
            height: 44,
            borderRadius: '12px',
            background: actionGradient,
            color: isBuy ? '#07090e' : '#ffffff',
            fontSize: '0.88rem',
            fontWeight: 800,
            textTransform: 'none',
            boxShadow: `0 8px 20px ${actionColor}25`,
            '&:hover': {
              background: actionGradient,
              opacity: 0.92,
              boxShadow: `0 12px 28px ${actionColor}35`,
              transform: 'translateY(-1.5px)'
            },
            '&:active': {
              transform: 'translateY(0)'
            },
            '&.Mui-disabled': {
              bgcolor: 'rgba(148, 163, 184, 0.08)',
              color: 'rgba(148, 163, 184, 0.3)',
              boxShadow: 'none'
            }
          }}
        >
          {loading ? (
            <CircularProgress size={20} sx={{ color: isBuy ? '#07090e' : '#ffffff' }} />
          ) : (
            isBuy ? 'ส่งคำสั่งซื้อ' : 'ส่งคำสั่งขาย'
          )}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
