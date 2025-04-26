import React, { useState, useRef, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import './FAQPage.css';
import logo from '../assets/logo.png';
import whatsappDemo1 from '../assets/Whatsappdemo/Whatsappdemo1.jpg';
import whatsappDemo2 from '../assets/Whatsappdemo/Whatsappdemo2.jpg';
import whatsappDemo3 from '../assets/Whatsappdemo/Whatsappdemo3.jpg';
import instaDemo1 from '../assets/Instademo/Instademo1.jpg';
import instaDemo2 from '../assets/Instademo/Instademo2.jpg';
import instaDemo3 from '../assets/Instademo/Instademo3.jpg';
import instaDemo4 from '../assets/Instademo/Instademo4.jpg';
import instaDemo5 from '../assets/Instademo/Instademo5.jpg';
import instaDemo6 from '../assets/Instademo/Instademo6.jpg';
import instaDemo7 from '../assets/Instademo/Instademo7.jpg';
import instaDemo8 from '../assets/Instademo/Instademo8.jpg';
import instaDemo9 from '../assets/Instademo/Instademo9.jpg';
import discDemo1 from '../assets/Discdemo/Discdemo1.jpg';
import discDemo2 from '../assets/Discdemo/Discdemo2.jpg';
import discDemo3 from '../assets/Discdemo/Discdemo3.jpg';

const faqData = {
  "General": [
    {
      question: "What is MindBack?",
      answer: "MindBack is an application designed to help you reconnect with your past self by interacting with your digital memories (social media posts, emails, photos, journal entries) through a conversational AI."
    },
    {
      question: "How does the conversation work?",
      answer: "The AI analyzes your imported memories from a specific year you select. It adopts a persona based on that year's data and allows you to ask questions or reflect on that period of your life."
    },
     {
      question: "How is the 'Past Self' persona generated?",
      answer: "The persona is generated based on the content, sentiment, and context extracted from your memories of the selected year. The 'Temperature' setting in Settings can adjust the creativity and strictness of the persona's adherence to the data."
    },
    {
      question: "Can I talk to different years simultaneously?",
      answer: "Yes! You can open multiple conversation tabs, each focused on a different year, allowing you to explore different periods of your past side-by-side."
    }
  ],
  "Data & Security": [
     {
      question: "Is my data secure?",
      answer: "Data security is a top priority. Your imported data is processed locally where possible, and any cloud interactions are handled with strict privacy measures. We do not sell or share your personal data. [Note: This is a placeholder answer - specific security details depend on implementation]."
    },
    {
      question: "What data sources can I import?",
      answer: "Currently, MindBack supports manual file uploads. Future versions may include direct integrations with platforms like Google Photos, Facebook, etc. (Functionality depends on implementation)."
    }
  ],
  "How to Upload Data From...": [
    {
      question: "WhatsApp",
      answer: { type: 'images', images: [whatsappDemo1, whatsappDemo2, whatsappDemo3] }
    },
    {
      question: "Instagram and Facebook",
      answer: { type: 'images', images: [instaDemo1, instaDemo2, instaDemo3, instaDemo4, instaDemo5, instaDemo6, instaDemo7, instaDemo8, instaDemo9] }
    },
    {
      question: "Discord",
      answer: { type: 'images', images: [discDemo1, discDemo2, discDemo3] }
    }
  ]
};

const FAQPage = () => {
  const navigate = useNavigate();
  const [openIndex, setOpenIndex] = useState(null);
  const itemRefs = useRef([]);
  const scrollContainerRef = useRef(null);

  const toggleFAQ = (index) => {
    const newOpenIndex = openIndex === index ? null : index;
    setOpenIndex(newOpenIndex);

    setTimeout(() => {
      if (newOpenIndex !== null && itemRefs.current[newOpenIndex]) {
        itemRefs.current[newOpenIndex].scrollIntoView({
          behavior: 'smooth',
          block: 'start',
          behavior: 'smooth',
        });
      }
    }, 100);
  };

  let flatIndex = 0;
  const allFaqs = Object.entries(faqData).flatMap(([category, items]) => [
    { type: 'category', title: category, id: `cat-${category}` },
    ...items.map(item => ({ ...item, type: 'item', id: flatIndex++ }))
  ]);

  return (
    <div className="faq-page-container">
      <header className="faq-page-header">
        <button onClick={() => navigate(-1)} className="back-link-faq">← Back</button>
        <h1>FAQ</h1>
        <Link to="/" className="faq-logo-link">
          <img src={logo} alt="MindBack Logo" className="faq-logo" />
        </Link>
      </header>
      <div className="faq-page-content" ref={scrollContainerRef}>
        {allFaqs.map((item) => {
          const itemIndex = item.type === 'item' ? item.id : null;
          if (item.type === 'category') {
            return <h2 key={item.id} className="faq-category-title">{item.title}</h2>;
          }
          const isOpen = openIndex === itemIndex;
          return (
            <div
              key={item.id}
              className="faq-item"
              ref={el => { if(itemIndex !== null) itemRefs.current[itemIndex] = el; }}
              aria-expanded={isOpen}
            >
              <button className="faq-question-button" onClick={() => toggleFAQ(itemIndex)}>
                <span className="faq-question-text">{item.question}</span>
                <span className={`faq-toggle-icon ${isOpen ? 'open' : ''}`}>▼</span>
              </button>
              {isOpen && (
                <div className="faq-answer">
                  {typeof item.answer === 'object' && item.answer.type === 'images' ? (
                    item.answer.images.map((imgSrc, imgIndex) => (
                      <img
                        key={imgIndex}
                        src={imgSrc}
                        alt={`${item.question} Step ${imgIndex + 1}`}
                        className="faq-image"
                      />
                    ))
                  ) : (
                    <p>{item.answer}</p>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default FAQPage;
