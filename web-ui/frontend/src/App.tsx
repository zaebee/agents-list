// Main App component

import React from 'react';
import { ToastContainer } from 'react-toastify';
import Dashboard from './components/Dashboard';
import 'react-toastify/dist/ReactToastify.css';

function App() {
  return (
    <div className="App">
      <Dashboard />
      
      {/* Toast notifications */}
      <ToastContainer
        position="top-right"
        autoClose={5000}
        hideProgressBar={false}
        newestOnTop={false}
        closeOnClick
        rtl={false}
        pauseOnFocusLoss
        draggable
        pauseOnHover
        theme="light"
      />
    </div>
  );
}

export default App;