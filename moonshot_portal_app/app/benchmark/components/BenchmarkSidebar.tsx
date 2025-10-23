"use client"
import React from 'react';

interface BenchmarkSidebarProps {
  currentPage: 'bundle-selection' | 'model-selection';
}

export default function BenchmarkSidebar({ currentPage }: BenchmarkSidebarProps) {
  return (
    <div 
      style={{
        boxSizing: 'border-box',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'flex-start',
        padding: '121px 24px 16px',
        gap: '8px',
        isolation: 'isolate',
        position: 'fixed',
        width: '385px',
        height: '100vh',
        right: '0px',
        top: '0px',
        background: '#F8FAFC',
        borderLeft: '1px solid #E2E8F0'
      }}
    >
      {/* Sidebar content goes here */}
    </div>
  );
}
