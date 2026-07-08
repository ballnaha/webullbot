"use client";

import React from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Typography,
  Button,
  Box,
  CircularProgress,
  IconButton,
  Zoom
} from '@mui/material';
import { TransitionProps } from '@mui/material/transitions';
import { 
  AlertTriangle, 
  HelpCircle, 
  CheckCircle, 
  X 
} from 'lucide-react';

export type ConfirmSeverity = 'info' | 'warning' | 'error' | 'success';

// Smooth zoom transition for the dialog
const Transition = React.forwardRef(function Transition(
  props: TransitionProps & {
    children: React.ReactElement<any, any>;
  },
  ref: React.Ref<unknown>,
) {
  return <Zoom ref={ref} {...props} />;
});

interface ConfirmDialogProps {
  open: boolean;
  title: React.ReactNode;
  message: React.ReactNode;
  confirmText?: string;
  cancelText?: string;
  onConfirm: () => void;
  onCancel: () => void;
  loading?: boolean;
  severity?: ConfirmSeverity;
}

export default function ConfirmDialog({
  open,
  title,
  message,
  confirmText = 'ยืนยัน',
  cancelText = 'ยกเลิก',
  onConfirm,
  onCancel,
  loading = false,
  severity = 'info'
}: ConfirmDialogProps) {

  // Color selection based on severity
  const getSeverityColors = () => {
    switch (severity) {
      case 'warning':
        return {
          main: '#f0a020',
          gradient: 'linear-gradient(135deg, #f0a020, #e08c00)',
          text: '#07090e'
        };
      case 'error':
        return {
          main: '#ea3943',
          gradient: 'linear-gradient(135deg, #ea3943, #d6222b)',
          text: '#ffffff'
        };
      case 'success':
        return {
          main: '#16c784',
          gradient: 'linear-gradient(135deg, #16c784, #0fa56c)',
          text: '#07090e'
        };
      case 'info':
      default:
        return {
          main: '#3b82f6',
          gradient: 'linear-gradient(135deg, #3b82f6, #1d4ed8)',
          text: '#ffffff'
        };
    }
  };

  // Icon selection based on severity
  const getSeverityIcon = () => {
    const size = 30;
    const colors = getSeverityColors();
    switch (severity) {
      case 'warning':
        return <AlertTriangle size={size} color={colors.main} />;
      case 'error':
        return <AlertTriangle size={size} color={colors.main} />;
      case 'success':
        return <CheckCircle size={size} color={colors.main} />;
      case 'info':
      default:
        return <HelpCircle size={size} color={colors.main} />;
    }
  };

  const colors = getSeverityColors();

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
            p: 2,
            position: 'relative',
            boxShadow: `0 24px 60px -10px rgba(0, 0, 0, 0.85), 0 0 40px ${colors.main}0a`,
            overflow: 'hidden',
            // Decorative accent line at the top
            '&::before': {
              content: '""',
              position: 'absolute',
              top: 0,
              left: 0,
              right: 0,
              height: '4px',
              background: colors.gradient
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

      {/* Dialog Header with Icon */}
      <DialogTitle component="div" sx={{ p: 2.5, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2, textAlign: 'center' }}>
        <Box
          sx={{
            width: 72,
            height: 72,
            borderRadius: '22px', // Modern squircle look
            bgcolor: `${colors.main}12`, // 7% opacity background
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            border: `1.5px solid ${colors.main}25`,
            boxShadow: `0 8px 24px ${colors.main}15`,
            mb: 0.5,
            position: 'relative'
          }}
        >
          {getSeverityIcon()}
        </Box>
        <Typography 
          variant="h6" 
          sx={{ 
            fontWeight: 800, 
            color: '#f8fafc', 
            letterSpacing: '-0.01em', 
            lineHeight: 1.3,
            px: 1
          }}
        >
          {title}
        </Typography>
      </DialogTitle>

      {/* Dialog Message */}
      <DialogContent sx={{ px: 3, pb: 1.5, textAlign: 'center' }}>
        <Typography 
          variant="body2" 
          color="text.secondary" 
          sx={{ 
            fontSize: '0.94rem', 
            lineHeight: 1.6,
            fontWeight: 500,
            letterSpacing: '0.015em'
          }}
        >
          {message}
        </Typography>
      </DialogContent>

      {/* Dialog Action Buttons */}
      <DialogActions sx={{ p: 2.5, display: 'flex', gap: 2, justifyContent: 'center' }}>
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
            transition: 'all 0.25s',
            bgcolor: 'rgba(255, 255, 255, 0.01)',
            '&:hover': {
              borderColor: 'rgba(148, 163, 184, 0.25)',
              bgcolor: 'rgba(255, 255, 255, 0.03)',
              color: '#f8fafc'
            }
          }}
        >
          {cancelText}
        </Button>
        <Button
          onClick={onConfirm}
          disabled={loading}
          variant="contained"
          sx={{
            flex: 1,
            height: 44,
            borderRadius: '12px',
            background: colors.gradient,
            color: colors.text,
            fontSize: '0.88rem',
            fontWeight: 800,
            textTransform: 'none',
            transition: 'all 0.25s',
            boxShadow: `0 8px 20px ${colors.main}25`,
            border: 'none',
            '&:hover': {
              background: colors.gradient,
              opacity: 0.92,
              boxShadow: `0 12px 28px ${colors.main}35`,
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
            <CircularProgress size={20} sx={{ color: colors.text }} />
          ) : (
            confirmText
          )}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
