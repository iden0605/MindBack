import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import Sidebar from '../components/Sidebar';
import ConversationInterface from '../components/ConversationInterface';
import CustomYearDropdown from '../components/CustomYearDropdown';
import ParticipantDropdown from '../components/ParticipantDropdown';
import { Link } from 'react-router-dom';
import '../App.css';
import { v4 as uuidv4 } from 'uuid';
import logo from '../assets/logo.png';

const MAX_TABS = 5;

const MainApp = ({ uploadedFiles, handleFilesUpdate }) => {
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);

  useEffect(() => {
    const clearDataOnLoad = async () => {
      try {
        const response = await fetch('http://127.0.0.1:5000/api/clear_uploaded_files', {
          method: 'POST',
        });
        const data = await response.json();
        if (response.ok) {
          console.log('Backend data cleared on page load:', data.message);
        } else {
          console.error('Failed to clear backend data on page load:', data.error);
        }
      } catch (error) {
        console.error('Network error clearing backend data on page load:', error);
      }
    };
    clearDataOnLoad();
  }, []);

  const [selectedYear, setSelectedYear] = useState(new Date().getFullYear());
  const [isLoading, setIsLoading] = useState(true);
  const [view, setView] = useState('default');
  const [tabs, setTabs] = useState([]);
  const [activeTabId, setActiveTabId] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingProgress, setProcessingProgress] = useState(0);
  const [availableYears, setAvailableYears] = useState([]);
  const [unprocessedFiles, setUnprocessedFiles] = useState([]);
  const [participantsByYear, setParticipantsByYear] = useState({});
  const [processingText, setProcessingText] = useState('Processing Data.');
  const [activeTabParticipants, setActiveTabParticipants] = useState({});
  const [isLoadingActiveTabParticipants, setIsLoadingActiveTabParticipants] = useState(false);
  const [activeTabTempSelectedUsers, setActiveTabTempSelectedUsers] = useState({});

  useEffect(() => {
    const initializeApp = async () => {
      setIsLoading(true);
      setAvailableYears([]);
      setParticipantsByYear({});

      try {
        const yearsResponse = await fetch('http://127.0.0.1:5000/api/get_available_years');
        const yearsData = await yearsResponse.json();
        console.log('Response from /api/get_available_years:', yearsResponse.status, yearsData);

        if (yearsResponse.ok && yearsData && Array.isArray(yearsData)) {
          const fetchedYears = yearsData;
          setAvailableYears(fetchedYears);

          const participantsData = {};
          for (const year of fetchedYears) {
            try {
              const participantsResponse = await fetch(`http://127.0.0.1:5000/api/get_participants/${year}`);
              const participantsJson = await participantsResponse.json();
              if (participantsResponse.ok && participantsJson.participants_by_source) {
                 const uniqueParticipants = new Set();
                 Object.values(participantsJson.participants_by_source).forEach(participantsList => {
                     participantsList.forEach(name => uniqueParticipants.add(name));
                 });
                 participantsData[year] = Array.from(uniqueParticipants);
              } else {
                console.warn(`Failed to fetch participants for year ${year}:`, participantsJson.error || 'Unknown error');
                participantsData[year] = [];
              }
            } catch (participantError) {
              console.error(`Network error fetching participants for year ${year}:`, participantError);
              participantsData[year] = [];
            }
          }
          setParticipantsByYear(participantsData);
          if (fetchedYears.length > 0) {
              setView('default');
          } else {
              setView('default');
          }

        } else {
          console.error('Failed to fetch available years or data format incorrect:', yearsData);
          setView('default');
        }
      } catch (error) {
        console.error('Network error fetching available years:', error);
        setView('default');
      } finally {
        setIsLoading(false);
      }
    };

    initializeApp();
  }, []);

  useEffect(() => {
      let intervalId;
      if (isProcessing) {
          const texts = ['Processing Data.', 'Processing Data..', 'Processing Data...'];
          let index = 0;
          intervalId = setInterval(() => {
              setProcessingText(texts[index]);
              index = (index + 1) % texts.length;
          }, 500);
      } else {
          setProcessingText('Processing Data.');
      }

      return () => {
          if (intervalId) {
              clearInterval(intervalId);
          }
      };
  }, [isProcessing]);

  const handleProcessData = async () => {
    setIsProcessing(true);
    setProcessingProgress(0);
    setView('processing');

    try {
      const response = await fetch('http://127.0.0.1:5000/api/process_data', {
        method: 'POST',
      });

      let simulatedProgress = 0;
      const progressInterval = setInterval(() => {
          simulatedProgress += 10;
          if (simulatedProgress <= 100) {
              setProcessingProgress(simulatedProgress);
          }
      }, 200);

      const data = await response.json();
      clearInterval(progressInterval);
      setProcessingProgress(100);

      if (response.ok) {
        console.log('Processing successful:', data.message);
        console.log('Available years after processing:', data.available_years);
        console.log('Unprocessed files:', data.unprocessed_files);
        const updatedAvailableYears = data.available_years || [];
        setAvailableYears(updatedAvailableYears);
        setUnprocessedFiles(data.unprocessed_files || []);

        const processedYears = data.available_years || [];
        if (processedYears.length > 0) {
            const latestYear = Math.max(...processedYears);
            addTab(latestYear);
        } else {
            console.warn("No available years returned after processing. User needs to manually select.");
            setView('default');
            alert('Data processing complete, but no available years found. Please check uploaded files.');
        }

      } else {
        console.error('Processing failed:', data.error);
        setView('default');
        alert(`Data processing failed: ${data.error}`);
      }
    } catch (error) {
      console.error('Network error during processing:', error);
      setView('default');
      alert(`Network error during data processing: ${error}`);
    } finally {
      setIsProcessing(false);
    }
  };

  useEffect(() => {
      const fetchParticipantsForTab = async () => {
          const currentActiveTab = tabs.find(tab => tab.id === activeTabId);
          if (!currentActiveTab || !currentActiveTab.year || Object.keys(currentActiveTab.selectedUserNames).length > 0) {
              setActiveTabParticipants({});
              setActiveTabTempSelectedUsers({});
              return;
          }

          setIsLoadingActiveTabParticipants(true);
          console.log(`Fetching participants for active tab year: ${currentActiveTab.year}`);

          try {
              const response = await fetch(`http://127.0.0.1:5000/api/get_participants/${currentActiveTab.year}`);
              const data = await response.json();

              if (response.ok) {
                  console.log('Participants fetched for active tab:', data.participants_by_source);
                  setActiveTabParticipants(data.participants_by_source || {});
                  const initialTempSelections = {};
                   for (const source in data.participants_by_source) {
                       initialTempSelections[source] = '';
                   }
                  setActiveTabTempSelectedUsers(initialTempSelections);

              } else {
                  console.error('Failed to fetch participants for active tab:', data.error);
                  setActiveTabParticipants({});
                  setActiveTabTempSelectedUsers({});
              }
          } catch (error) {
              console.error('Network error fetching participants for active tab:', error);
              setActiveTabParticipants({});
              setActiveTabTempSelectedUsers({});
          } finally {
              setIsLoadingActiveTabParticipants(false);
          }
      };

      fetchParticipantsForTab();

  }, [activeTabId, tabs]);

  const addTab = (yearToAdd = selectedYear) => {
    if (tabs.length >= MAX_TABS) {
      alert(`Maximum of ${MAX_TABS} tabs reached.`);
      return;
    }
    const newTabId = uuidv4();
    const newTab = {
      id: newTabId,
      year: yearToAdd,
      messages: [],
      selectedUserNames: {},
      isTyping: false
    };
    setTabs([...tabs, newTab]);
    setActiveTabId(newTabId);
    setView('conversation');
  };

  const switchTab = (tabId) => {
    setActiveTabId(tabId);
    setView('conversation');
  };

  const closeTab = (tabIdToClose) => {
    if (tabs.length === 1) {
      console.log("Cannot close the last tab.");
      return;
    }

    const tabIndex = tabs.findIndex(tab => tab.id === tabIdToClose);
    if (tabIndex === -1) return;

    const newTabs = tabs.filter(tab => tab.id !== tabIdToClose);
    setTabs(newTabs);

    if (activeTabId === tabIdToClose) {
      if (newTabs.length > 0) {
        const newActiveIndex = Math.max(0, tabIndex - 1);
        setActiveTabId(newTabs[newActiveIndex].id);
      } else {
        setActiveTabId(null);
        setView('default');
      }
    }
  };

  const updateTabMessages = (tabId, newMessages) => {
    setTabs(currentTabs =>
      currentTabs.map(tab =>
        tab.id === tabId ? { ...tab, messages: newMessages } : tab
      )
    );
  };

  const updateTabTypingState = (tabId, isTyping) => {
      setTabs(currentTabs =>
          currentTabs.map(tab =>
              tab.id === tabId ? { ...tab, isTyping: isTyping } : tab
          )
      );
  };

  const updateTabYear = (tabId, newYear) => {
     setTabs(currentTabs =>
      currentTabs.map(tab =>
        tab.id === tabId ? { ...tab, year: newYear, messages: [], selectedUserNames: {} } : tab
      )
    );
  };

  const updateTabSelectedUserNames = (tabId, newSelectedUserNames) => {
      setTabs(currentTabs =>
          currentTabs.map(tab =>
              tab.id === tabId ? { ...tab, selectedUserNames: newSelectedUserNames, messages: [] } : tab
          )
      );
  };

  const handleActiveTabUserSelectChange = (sourceType, selectedName) => {
      setActiveTabTempSelectedUsers(prevNames => ({
          ...prevNames,
          [sourceType]: selectedName
      }));
  };

  const handleConfirmActiveTabPersona = async () => {
      const currentActiveTab = tabs.find(tab => tab.id === activeTabId);
      if (!currentActiveTab) return;

      for (const source in activeTabParticipants) {
          if (activeTabParticipants[source].length > 0 && !activeTabTempSelectedUsers[source]) {
              alert(`Please select your name for ${source.capitalize()}.`);
              return;
          }
      }

      console.log('Sending user names to backend:', {
          year: activeTab.year,
          selected_user_names: activeTabTempSelectedUsers,
      });
      try {
          const response = await fetch('http://127.0.0.1:5000/api/set_user_names', {
              method: 'POST',
              headers: {
                  'Content-Type': 'application/json',
              },
              body: JSON.stringify({
                  year: activeTab.year,
                  selected_user_names: activeTabTempSelectedUsers,
              }),
          });

          const data = await response.json();

          if (response.ok) {
              console.log('Backend user names set successfully:', data.message);
              updateTabSelectedUserNames(activeTab.id, activeTabTempSelectedUsers);
          } else {
              console.error('Failed to set user names on backend:', data.error);
              alert(`Error setting user names: ${data.error}`);
          }
      } catch (error) {
          console.error('Network error setting user names:', error);
          alert(`Network error setting user names: ${error}`);
      }
  };

  const handleStartConversation = (yearToConverse = selectedYear) => {
    const existingTab = tabs.find(tab => tab.year === yearToConverse);

    if (existingTab) {
      switchTab(existingTab.id);
    } else if (tabs.length < MAX_TABS) {
      addTab(yearToConverse);
    } else {
      alert(`Maximum of ${MAX_TABS} tabs reached. Please close a tab to start a new conversation.`);
      if (tabs.length > 0 && !activeTabId) {
         setActiveTabId(tabs[0].id);
         setView('conversation');
      } else if (tabs.length > 0) {
         setView('conversation');
      } else {
         setView('default');
      }
    }
  };

  const toggleSidebar = () => {
    setIsSidebarCollapsed(!isSidebarCollapsed);
  };

  const fadeInVariants = {
    hidden: {
      opacity: 0,
      y: 20
    },
    visible: {
      opacity: 1,
      y: 0,
      transition: { duration: 0.8, ease: "easeOut" }
    },
    exit: {
      opacity: 0,
      y: -10,
      transition: { duration: 0.3, ease: "easeIn" }
    }
  };

  const sidebarVariants = fadeInVariants;
  const conversationVariants = fadeInVariants;

  const activeTab = tabs.find(tab => tab.id === activeTabId);

  console.log('Current view state:', view);

  let mainContentArea;

  if (isLoading) {
      mainContentArea = (
          <div className="loading">Loading your memories...</div>
      );
  } else if (isProcessing) {
      mainContentArea = (
          <div className="processing-view">
              <h2>{processingText}</h2>
              <p>This may take a few moments depending on the size of your files.</p>
              {processingProgress === 100 && unprocessedFiles.length > 0 && (
                  <div className="unprocessed-files-list">
                      <h3>Could not process the following files:</h3>
                      <ul>
                          {unprocessedFiles.map((fileName, index) => (
                              <li key={index}>{fileName}</li>
                          ))}
                      </ul>
                  </div>
              )}
          </div>
      );
  } else if (view === 'default') {
       mainContentArea = (
           <div className="no-data-message">
               <h2>Welcome to MindBack</h2>
               {isLoading ? (
                   <p>Loading available data...</p>
               ) : availableYears.length > 0 ? (
                   <p>Select a year from the sidebar to start a conversation or upload/process more data.</p>
               ) : (
                   <p>Upload your social media data or process existing uploads to get started.</p>
               )}
           </div>
       );
  } else if (view === 'conversation' && activeTab) {
      if (Object.keys(activeTab.selectedUserNames).length === 0) {
          mainContentArea = (
              <div className="persona-selection-view">
                  <h2>Select Your Persona for {activeTab.year}</h2>
                  <p className="persona-selection-subtitle">Identify yourself in the data sources for this year.</p>

                   <div className="year-selection">
                       <label htmlFor="select-year-tab">Select a Year:</label>
                       <CustomYearDropdown
                           selectedYear={activeTab.year}
                           years={availableYears}
                           onYearSelect={(newYear) => updateTabYear(activeTab.id, newYear)}
                           dropdownId={`select-year-tab-${activeTab.id}`}
                       />
                   </div>

                  {isLoadingActiveTabParticipants ? (
                      <div className="loading-participants">Loading participants for {activeTab.year}...</div>
                  ) : Object.keys(activeTabParticipants).length > 0 ? (
                      <div className="participant-selection">
                          <h3>Identify Yourself in Each Source:</h3>
                          {Object.entries(activeTabParticipants).map(([sourceType, participants]) => (
                              <div key={sourceType} className="source-participant-select">
                                  <label htmlFor={`select-${sourceType}-${activeTab.id}`}>{sourceType.charAt(0).toUpperCase() + sourceType.slice(1)}:</label>
                                  {participants.length > 0 ? (
                                      <select
                                          id={`select-${sourceType}-${activeTab.id}`}
                                          value={activeTabTempSelectedUsers[sourceType] || ''}
                                          onChange={(e) => handleActiveTabUserSelectChange(sourceType, e.target.value)}
                                      >
                                          <option value="" disabled>-- Select Your Name --</option>
                                          {participants.map(name => (
                                              <option key={name} value={name}>{name}</option>
                                          ))}
                                      </select>
                                    ) : (
                                      <p className="no-participants-found">No specific participants found for {sourceType}.</p>
                                    )}
                              </div>
                          ))}
                      </div>
                  ) : (
                       <div className="no-participants-message">No participants found for {activeTab.year}.</div>
                  )}

                  {Object.keys(activeTabParticipants).length > 0 && (
                      <button
                          className="action-btn btn-primary confirm-persona-btn"
                          onClick={handleConfirmActiveTabPersona}
                          disabled={Object.keys(activeTabParticipants).some(source =>
                              activeTabParticipants[source].length > 0 && !activeTabTempSelectedUsers[source]
                          )}
                      >
                          Confirm Persona & Start Chat
                      </button>
                  )}
              </div>
          );
      } else {
          mainContentArea = (
              <ConversationInterface
                  tabs={tabs}
                  activeTabId={activeTabId}
                  onSwitchTab={switchTab}
                  selectedUserNames={activeTab.selectedUserNames}
                  onUpdateSelectedUserNames={(newNames) => updateTabSelectedUserNames(activeTab.id, newNames)}
                  onCloseTab={closeTab}
                  onAddTab={addTab}
                  onUpdateTabMessages={updateTabMessages}
                  onUpdateTabYear={updateTabYear}
                  onUpdateTabTypingState={updateTabTypingState}
                  maxTabs={MAX_TABS}
              />
          );
      }
  } else {
       mainContentArea = (
          <div className="no-data-message">
              <h2>Welcome to MindBack</h2>
              <p>Upload your social media data to get started.</p>
          </div>
      );
  }

  return (
    <div className={`app-layout ${isSidebarCollapsed ? 'sidebar-collapsed' : ''}`}>
      <header className="app-header">
         <button onClick={toggleSidebar} className="sidebar-toggle-btn">
           {isSidebarCollapsed ? '☰' : '✕'}
         </button>
        <Link to="/" className="nav-link app-title-link">
          MindBack
          <img src={logo} alt="MindBack Logo" className="header-logo" />
        </Link>
        <nav className="app-nav">
          <Link to="/faq" className="nav-link">FAQ</Link>
        </nav>
      </header>
      <div className="main-content">
        <motion.div
          className="sidebar-container"
          initial="hidden"
          animate="visible"
          variants={sidebarVariants}
        >
          <Sidebar
            uploadedFiles={uploadedFiles}
            handleFilesUpdate={handleFilesUpdate}
            onUploadCompleteAndProcess={handleProcessData}
            availableYears={availableYears}
            onStartConversation={handleStartConversation}
          />
        </motion.div>
        <motion.div
          className="content-area"
          initial="hidden"
          animate="visible"
          variants={fadeInVariants}
        >
          {mainContentArea}
        </motion.div>
      </div>
    </div>
  );
};

export default MainApp;
