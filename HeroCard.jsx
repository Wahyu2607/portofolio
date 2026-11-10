import React, { useState } from "react";

/**
 * HeroCard Component
 * Menampilkan kartu foto bergradasi ungu dengan foto programmer
 * dan floating code snippet card di atasnya (sesuai referensi ss.jpeg).
 */
export default function HeroCard({
  name = "Alex",
  skills = ["HTML", "CSS", "JavaScript", "React"],
  passion = "Building things for the web",
  imageSrc = "./Untitled design.png"
}) {
  return (
    <div className="relative w-[380px] sm:w-[460px] lg:w-[500px] select-none">
      {/* 1. Main Profile Cutout (Tanpa Background Box - Ukuran Lebih Besar & Muka Jelas) */}
      <div className="relative w-full h-[540px] sm:h-[600px] bg-transparent overflow-visible flex items-end justify-center">
        {/* Foto Programmer Cutout */}
        <img
          src={imageSrc}
          alt={`${name} portrait`}
          className="w-full h-full object-contain object-bottom drop-shadow-[0_25px_45px_rgba(0,0,0,0.85)] drop-shadow-[0_0_35px_rgba(139,92,246,0.35)] transition-transform duration-700 hover:scale-105"
        />
      </div>

      {/* 2. Floating Code Snippet Card (Di sisi kanan atas luar tanpa menutupi foto/muka) */}
      <div className="absolute -right-4 sm:-right-12 top-6 sm:top-8 w-[220px] sm:w-[240px] bg-[#121625]/90 backdrop-blur-xl border border-slate-700/60 rounded-2xl p-4 sm:p-5 shadow-[0_25px_50px_-12px_rgba(0,0,0,0.7),0_0_30px_-10px_rgba(99,102,241,0.2)] z-20 font-mono transition-all duration-300 hover:translate-y-[-4px]">
        
        {/* Header </> Code & Green Status Dot */}
        <div className="flex items-center justify-between mb-3 pb-2 border-b border-slate-700/50">
          <div className="flex items-center gap-2 text-[#7f8ee8] font-semibold text-xs tracking-wide">
            <span className="text-indigo-400 font-bold">&lt;/&gt;</span>
            <span className="text-slate-300">Code</span>
          </div>
          <div className="flex items-center gap-1.5" title="Active">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
            </span>
          </div>
        </div>

        {/* Syntax Highlighted Code Object */}
        <div className="space-y-1 text-[11px] sm:text-xs leading-relaxed font-mono">
          <p>
            <span className="text-purple-400 font-semibold">const</span>{" "}
            <span className="text-slate-200">developer</span>{" "}
            <span className="text-slate-400">=</span>{" "}
            <span className="text-slate-300">&#123;</span>
          </p>
          <p className="pl-4">
            <span className="text-sky-300">name</span>
            <span className="text-slate-400">:</span>{" "}
            <span className="text-[#7fe8a3]">"{name}"</span>
            <span className="text-slate-400">,</span>
          </p>
          <p className="pl-4">
            <span className="text-sky-300">skills</span>
            <span className="text-slate-400">:</span>{" "}
            <span className="text-slate-300">[</span>
            {skills.map((skill, index) => (
              <span key={skill}>
                <span className="text-[#7fe8a3]">"{skill}"</span>
                {index < skills.length - 1 && (
                  <span className="text-slate-400">, </span>
                )}
              </span>
            ))}
            <span className="text-slate-300">]</span>
            <span className="text-slate-400">,</span>
          </p>
          <p className="pl-4">
            <span className="text-sky-300">passion</span>
            <span className="text-slate-400">:</span>{" "}
            <span className="text-[#7fe8a3]">"{passion}"</span>
          </p>
          <p>
            <span className="text-slate-300">&#125;;</span>
          </p>
        </div>
      </div>

      {/* 3. Bottom Status Pill */}
      <div className="absolute -bottom-4 left-6 bg-[#131728]/90 backdrop-blur-md border border-slate-700/60 rounded-full px-4 py-1.5 flex items-center gap-2 text-xs font-mono text-slate-300 shadow-xl z-20">
        <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
        <span className="text-emerald-400 font-semibold">Online</span>
        <span className="text-slate-500">|</span>
        <span className="text-slate-400">Laptop Ready</span>
      </div>
    </div>
  );
}
