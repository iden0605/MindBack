import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import './HomePage.css';
import logo from '../assets/logo.png';

const HomePage = ({ message }) => {

  return (
    <div className="home-page">
      <header className="home-header">
        <Link to="/" className="home-logo-link">
          <img src={logo} alt="MindBack Logo" className="home-logo" />
        </Link>
        <nav className="home-nav">
          <Link to="/faq" className="nav-link">FAQ</Link>
        </nav>
      </header>
      <main className="home-content">
        <h1>MindBack</h1>
        <p>reconnect with your past self or friends</p>
        <Link to="/app" className="enter-app-link">Start Exploring</Link>

        <section className="home-description">
          <h2>What is MindBack?</h2>
          <p>
            MindBack offers a unique way to journey through your personal history.
            Upload your digital memories from supported platforms including Instagram, Facebook, Discord, and WhatsApp.
            Please ensure your data is provided in zip file format. A detailed guide on how to export your data in this format can be found on our FAQ page.
          </p>
          <p>
            Select a year, and our specialized AI analyzes the content, tone, and context
            to create a conversational 'past self or friends' persona reflecting who you were then.
          </p>
          <p>
            Engage with this persona. Ask questions about forgotten events, explore old perspectives,
            or simply reflect on your experiences from that time. It's a powerful tool for
            self-discovery and understanding your personal evolution.
            This application can also serve as a valuable tool in aiding individuals with dementia by providing a structured way to revisit and engage with their past.
          </p>
        </section>
      </main>
    </div>
  );
};

export default HomePage;
