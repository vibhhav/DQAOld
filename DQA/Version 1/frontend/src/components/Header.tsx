
import React from 'react';
import { Link } from 'react-router-dom';

const Header = () => {
  return (
    <header className="w-full bg-white border-b border-gray-200">
      <div className="container mx-auto px-4 py-4 flex justify-between items-center">
        <div className="flex items-center gap-2">
          {/* <div className="h-8 w-8 bg-gold-500 rounded-full flex items-center justify-center">
            <span className="text-white font-bold text-lg">D</span>
          </div> */}
          <h1 className="text-xl font-bold">Design Quality Assurance</h1>
        </div>
        <nav>
          <ul className="flex items-center gap-6">
            <li>
              <Link to="/" className="text-sm font-medium text-gray-600 hover:text-gray-900">
                Home
              </Link>
            </li>
            <li>
              <Link to="/design-quality-assurance" className="text-sm font-medium text-gold-600 hover:text-gold-800">
                Evaluate Design
              </Link>
            </li>
          </ul>
        </nav>
      </div>
    </header>
  );
};

export default Header;
