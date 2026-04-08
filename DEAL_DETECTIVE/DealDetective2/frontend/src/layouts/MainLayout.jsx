import React from 'react';
import Navbar from '../components/layout/Navbar';

const MainLayout = ({ children }) => {
    return (
        <div className="min-h-screen flex flex-col relative overflow-hidden bg-background bg-grid-pattern font-sans text-white">
            <Navbar />

            <main className="flex-1 w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-32 pb-12 flex flex-col relative z-10">
                {children}
            </main>

            {/* Ambient Background Effects */}
            <div className="fixed inset-0 pointer-events-none overflow-hidden z-0">
                {/* Primary Blob */}
                <div className="absolute top-[-10%] left-[-5%] w-[50vw] h-[50vw] bg-primary-glow/5 rounded-full blur-[100px] animate-pulse-slow" />

                {/* Secondary Blob */}
                <div className="absolute bottom-[-10%] right-[-5%] w-[40vw] h-[40vw] bg-secondary-glow/5 rounded-full blur-[100px] animate-pulse-slow delay-1000" />

                {/* Subtle Center Glow */}
                <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-[60vw] h-[60vw] bg-blue-900/5 rounded-full blur-[120px]" />
            </div>
        </div>
    );
};

export default MainLayout;
