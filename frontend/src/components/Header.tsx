"use client";

import React from 'react';
import { Box, Typography, Button } from '@mui/material';
import { Cpu } from 'lucide-react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

interface HeaderProps {
  connected: boolean;
  tradeMode: string;
}

export default function Header({ connected, tradeMode }: HeaderProps) {
  const pathname = usePathname();
  const isStockUs = pathname === '/stockus' || pathname === '/';
  const isHongKong = pathname === '/hongkong';
  const isSettings = pathname === '/settings';
  const isLogs = pathname === '/logs';

  return (
    <Box 
      sx={{ 
        display: "flex", 
        justifyContent: "space-between", 
        alignItems: "center",
        flexDirection: { xs: 'column', md: 'row' },
        gap: 3,
        mb: 4,
        p: 2.5,
        borderRadius: '16px',
        bgcolor: '#0f141c',
        border: '1px solid rgba(148, 163, 184, 0.08)',
        borderTop: '3px solid #3b82f6',
        boxShadow: '0 4px 20px -2px rgba(0, 0, 0, 0.4)'
      }}
    >
      {/* Brand Logo & Info (Metabot Design) */}
      <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
        <Box 
          sx={{
            background: 'linear-gradient(135deg, #3b82f6, #6366f1)',
            width: 42,
            height: 42,
            borderRadius: 2,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#fff',
            boxShadow: '0 4px 12px rgba(59,130,246,0.3)'
          }}
        >
          <Cpu size={22} />
        </Box>
        <Box>
          <Typography variant="h6" sx={{ fontWeight: 800, color: '#f1f5f9', letterSpacing: '-0.01em', lineHeight: 1.2 }}>
            Webull Trading Bot
          </Typography>
          <Typography variant="caption" color="text.secondary" sx={{ display: 'flex', alignItems: 'center', gap: 0.5, fontSize: '0.72rem', mt: 0.2 }}>
            <span style={{ display: 'inline-block', width: 6, height: 6, borderRadius: '50%', backgroundColor: '#3b82f6', marginRight: 4 }}></span>
            ระบบวิเคราะห์และเทรดอัตโนมัติ
          </Typography>
        </Box>
      </Box>
      
      {/* Navigation Buttons (Metabot Pill design) */}
      <Box sx={{ display: 'flex', gap: 1, bgcolor: 'rgba(0,0,0,0.15)', p: 0.5, borderRadius: '10px' }}>
        <Link href="/stockus" passHref style={{ textDecoration: 'none' }}>
          <Button
            size="small"
            sx={{ 
              fontSize: '0.8rem', 
              fontWeight: 700, 
              width: 125,
              height: 36,
              borderRadius: '8px',
              transition: 'all 0.25s',
              textTransform: 'none',
              ...(isStockUs ? {
                bgcolor: 'rgba(59, 130, 246, 0.15)',
                color: '#60a5fa',
                border: '1px solid rgba(59, 130, 246, 0.3)',
                '&:hover': {
                  bgcolor: 'rgba(59, 130, 246, 0.2)'
                }
              } : {
                color: '#94a3b8',
                border: '1px solid transparent',
                '&:hover': {
                  color: '#fff',
                  bgcolor: 'rgba(255,255,255,0.03)'
                }
              })
            }}
          >
            🇺🇸 ตลาดสหรัฐฯ
          </Button>
        </Link>
        <Link href="/hongkong" passHref style={{ textDecoration: 'none' }}>
          <Button
            size="small"
            sx={{ 
              fontSize: '0.8rem', 
              fontWeight: 700, 
              width: 125,
              height: 36,
              borderRadius: '8px',
              transition: 'all 0.25s',
              textTransform: 'none',
              ...(isHongKong ? {
                bgcolor: 'rgba(59, 130, 246, 0.15)',
                color: '#60a5fa',
                border: '1px solid rgba(59, 130, 246, 0.3)',
                '&:hover': {
                  bgcolor: 'rgba(59, 130, 246, 0.2)'
                }
              } : {
                color: '#94a3b8',
                border: '1px solid transparent',
                '&:hover': {
                  color: '#fff',
                  bgcolor: 'rgba(255,255,255,0.03)'
                }
              })
            }}
          >
            🇭🇰 ตลาดฮ่องกง
          </Button>
        </Link>
        <Link href="/settings" passHref style={{ textDecoration: 'none' }}>
          <Button
            size="small"
            sx={{ 
              fontSize: '0.8rem', 
              fontWeight: 700, 
              width: 125,
              height: 36,
              borderRadius: '8px',
              transition: 'all 0.25s',
              textTransform: 'none',
              ...(isSettings ? {
                bgcolor: 'rgba(59, 130, 246, 0.15)',
                color: '#60a5fa',
                border: '1px solid rgba(59, 130, 246, 0.3)',
                '&:hover': {
                  bgcolor: 'rgba(59, 130, 246, 0.2)'
                }
              } : {
                color: '#94a3b8',
                border: '1px solid transparent',
                '&:hover': {
                  color: '#fff',
                  bgcolor: 'rgba(255,255,255,0.03)'
                }
              })
            }}
          >
            ⚙️ ตั้งค่าบอท
          </Button>
        </Link>
        <Link href="/logs" passHref style={{ textDecoration: 'none' }}>
          <Button
            size="small"
            sx={{ 
              fontSize: '0.8rem', 
              fontWeight: 700, 
              width: 125,
              height: 36,
              borderRadius: '8px',
              transition: 'all 0.25s',
              textTransform: 'none',
              ...(isLogs ? {
                bgcolor: 'rgba(59, 130, 246, 0.15)',
                color: '#60a5fa',
                border: '1px solid rgba(59, 130, 246, 0.3)',
                '&:hover': {
                  bgcolor: 'rgba(59, 130, 246, 0.2)'
                }
              } : {
                color: '#94a3b8',
                border: '1px solid transparent',
                '&:hover': {
                  color: '#fff',
                  bgcolor: 'rgba(255,255,255,0.03)'
                }
              })
            }}
          >
            📜 บันทึกบอท
          </Button>
        </Link>
      </Box>

      {/* API Status Badge (Metabot status styling) */}
      <Box 
        sx={{ 
          display: 'flex', 
          alignItems: 'center', 
          gap: 1,
          px: 1.5,
          py: 0.7,
          borderRadius: '8px',
          bgcolor: connected ? 'rgba(16, 185, 129, 0.1)' : 'rgba(234, 57, 67, 0.1)',
          border: `1px solid ${connected ? 'rgba(16, 185, 129, 0.28)' : 'rgba(234, 57, 67, 0.28)'}`
        }}
      >
        <Box 
          sx={{ 
            width: 8, 
            height: 8, 
            borderRadius: '50%', 
            bgcolor: connected ? '#16c784' : '#ea3943',
            animation: connected ? 'pulse 2s infinite' : 'none',
            '@keyframes pulse': {
              '0%': { boxShadow: '0 0 0 0 rgba(22, 199, 132, 0.7)' },
              '70%': { boxShadow: '0 0 0 6px rgba(22, 199, 132, 0)' },
              '100%': { boxShadow: '0 0 0 0 rgba(22, 199, 132, 0)' }
            }
          }}
        />
        <Typography 
          variant="caption" 
          sx={{ 
            fontWeight: 800, 
            color: connected ? '#16c784' : '#ea3943',
            letterSpacing: '0.04em',
            fontSize: '0.68rem'
          }}
        >
          {connected ? `API ONLINE (${tradeMode})` : "API SERVER OFFLINE"}
        </Typography>
      </Box>
    </Box>
  );
}
