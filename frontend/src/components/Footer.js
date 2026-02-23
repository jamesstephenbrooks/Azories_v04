import React from 'react';
import { Link } from 'react-router-dom';

const Footer = ({ dark = false }) => {
  const bgClass = dark ? 'bg-gray-900 text-gray-400' : 'bg-gray-100 text-gray-600';
  const linkClass = dark ? 'hover:text-white' : 'hover:text-gray-900';

  return (
    <footer className={`${bgClass} py-8 px-4`}>
      <div className="max-w-6xl mx-auto">
        <div className="flex flex-col md:flex-row justify-between items-center gap-4">
          <div className="text-center md:text-left">
            <Link to="/" className={`text-xl font-bold ${dark ? 'text-white' : 'text-gray-900'}`}>
              Azories
            </Link>
            <p className="text-sm mt-1">Where Stories Come Alive</p>
          </div>

          <div className="flex flex-wrap justify-center gap-6 text-sm">
            <Link to="/library" className={linkClass}>Library</Link>
            <Link to="/terms" className={linkClass}>Terms of Service</Link>
            <Link to="/privacy" className={linkClass}>Privacy Policy</Link>
            <Link to="/contact" className={linkClass}>Contact</Link>
          </div>
        </div>

        <div className="mt-6 pt-6 border-t border-gray-700/30 text-center text-sm">
          <p>© {new Date().getFullYear()} Azories. All rights reserved.</p>
          <p className="mt-1">
            Contact us at{' '}
            <a href="mailto:books@azories.com" className={`${linkClass} underline`}>
              books@azories.com
            </a>
          </p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
