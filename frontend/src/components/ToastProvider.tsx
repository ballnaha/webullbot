"use client";

import React, { createContext, useContext, useState, useCallback } from 'react';
import { Snackbar, Alert, AlertColor, Box, Typography } from '@mui/material';
import { CheckCircle, AlertTriangle, Info, X } from 'lucide-react';

type ToastSeverity = 'success' | 'error' | 'warning' | 'info';

interface ToastContextType {
  showToast: (message: string, severity?: ToastSeverity, duration?: number) => void;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider');
  }
  return context;
}

interface ToastProviderProps {
  children: React.ReactNode;
}

export default function ToastProvider({ children }: ToastProviderProps) {
  const [open, setOpen] = useState(false);
  const [message, setMessage] = useState('');
  const [severity, setSeverity] = useState<ToastSeverity>('info');
  const [duration, setDuration] = useState(4000);

  const showToast = useCallback((msg: string, sev: ToastSeverity = 'info', dur = 4000) => {
    setMessage(msg);
    setSeverity(sev);
    setDuration(dur);
    setOpen(true);
  }, []);

  const handleClose = (event?: React.SyntheticEvent | Event, reason?: string) => {
    if (reason === 'clickaway') {
      return;
    }
    setOpen(false);
  };

  // Color selection based on severity
  const getSeverityColor = () => {
    switch (severity) {
      case 'success':
        return '#16c784';
      case 'error':
        return '#ea3943';
      case 'warning':
        return '#f0a020';
      case 'info':
      default:
        return '#3b82f6';
    }
  };

  // Icon selection based on severity
  const getSeverityIcon = () => {
    const size = 18;
    switch (severity) {
      case 'success':
        return <CheckCircle size={size} color="#16c784" />;
      case 'error':
        return <AlertTriangle size={size} color="#ea3943" />;
      case 'warning':
        return <AlertTriangle size={size} color="#f0a020" />;
      case 'info':
      default:
        return <Info size={size} color="#3b82f6" />;
    }
  };

  const themeColor = getSeverityColor();

  return (
    <ToastContext.Provider value={{ showToast }}>
      {children}
      <Snackbar
        open={open}
        autoHideDuration={duration}
        onClose={handleClose}
        anchorOrigin={{ vertical: 'top', horizontal: 'right' }}
        sx={{
          top: { xs: 16, sm: 24 },
          right: { xs: 16, sm: 24 },
        }}
      >
        <Alert
          onClose={handleClose}
          severity={severity as AlertColor}
          icon={false} // Disable default MUI icon
          sx={{
            width: '100%',
            minWidth: { xs: '280px', sm: '320px' },
            maxWidth: '450px',
            bgcolor: '#0f141c',
            backgroundImage: 'linear-gradient(180deg, #111827, #0f172a)',
            borderLeft: `4px solid ${themeColor}`,
            borderTop: '1px solid rgba(148, 163, 184, 0.08)',
            borderRight: '1px solid rgba(148, 163, 184, 0.08)',
            borderBottom: '1px solid rgba(148, 163, 184, 0.08)',
            borderRadius: '12px',
            color: '#f1f5f9',
            boxShadow: '0 10px 30px -5px rgba(0, 0, 0, 0.6)',
            p: 1.5,
            display: 'flex',
            alignItems: 'center',
            '& .MuiAlert-message': {
              flex: 1,
              p: 0,
              display: 'flex',
              alignItems: 'center',
              gap: 1.5
            },
            '& .MuiAlert-action': {
              p: 0,
              mr: -0.5,
              color: '#94a3b8',
              '&:hover': { color: '#f1f5f9' }
            }
          }}
        >
          {/* Custom Icon wrapper */}
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: 32,
              height: 32,
              borderRadius: '8px',
              bgcolor: `${themeColor}10`, // 10% opacity
              border: `1px solid ${themeColor}20`
            }}
          >
            {getSeverityIcon()}
          </Box>
          
          {/* Message Text */}
          <Typography 
            variant="body2" 
            sx={{ 
              fontWeight: 600, 
              fontSize: '0.88rem', 
              color: '#f1f5f9',
              lineHeight: 1.4
            }}
          >
            {message}
          </Typography>
        </Alert>
      </Snackbar>
    </ToastContext.Provider>
  );
}
