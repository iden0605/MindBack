import { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import './App.css';

import HomePage from './pages/HomePage';
import FAQpage from './pages/FAQpage';
import MainApp from './pages/MainApp';

function App() {
  const [message, setMessage] = useState('');

  const [uploadedFiles, setUploadedFiles] = useState([]);

  const location = useLocation();

  const handleFilesUpdate = (updateAction) => {
    setUploadedFiles(currentFiles => {
      let updatedFiles = [...currentFiles];

      if (updateAction.action === 'add') {
        const newFilesToAdd = updateAction.files
          .filter(newFile => newFile && newFile.name && !currentFiles.some(existingFile => existingFile.name === newFile.name))
          .map(newFile => ({
              name: newFile.name,
              size: newFile.size
          }));
        updatedFiles = [...currentFiles, ...newFilesToAdd];

      } else if (updateAction.action === 'remove') {
        updatedFiles = currentFiles.filter(file => file.name !== updateAction.fileName);
      }

      console.log("App.jsx: Updated uploadedFiles state:", updatedFiles);
      return updatedFiles;
    });
  };

  useEffect(() => {
    fetch('http://127.0.0.1:5000/api/test')
      .then(response => response.json())
      .then(data => setMessage(data.message));
  }, []);

  useEffect(() => {
    if (location.pathname !== '/app') {
      setUploadedFiles([]);
      console.log("App.jsx: Cleared uploadedFiles state due to route change.");
    }
  }, [location.pathname]);

  const pageVariants = {
    initial: { opacity: 0 },
    in: { opacity: 1 },
    out: { opacity: 0 }
  };

  const pageTransition = {
    type: "tween",
    ease: "anticipate",
    duration: 0.3
  };

  return (
    <AnimatePresence mode="wait">
      <Routes location={location} key={location.pathname}>
        <Route path="/" element={
          <motion.div initial="initial" animate="in" exit="out" variants={pageVariants} transition={pageTransition}>
            <HomePage
              message={message}
            />
          </motion.div>
        } />
        <Route path="/app" element={
          <motion.div initial="initial" animate="in" exit="out" variants={pageVariants} transition={pageTransition}>
            <MainApp
              uploadedFiles={uploadedFiles}
              handleFilesUpdate={handleFilesUpdate}
            />
          </motion.div>
        } />
         <Route path="/faq" element={
           <motion.div initial="initial" animate="in" exit="out" variants={pageVariants} transition={pageTransition}>
             <FAQpage />
           </motion.div>
         } />
       </Routes>
    </AnimatePresence>
  );
}

const AppWrapper = () => (
  <Router>
    <App />
  </Router>
);

export default AppWrapper;
