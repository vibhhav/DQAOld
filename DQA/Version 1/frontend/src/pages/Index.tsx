
import React from 'react';
import { Button } from '@/components/ui/button';
import { Link } from 'react-router-dom';
import { FileCheck, Upload, BarChart } from 'lucide-react';

const Index = () => {
  return (
    <div className="flex flex-col min-h-screen bg-gradient-to-b from-white to-gray-50">
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
                <Link to="/" className="text-sm font-medium text-gold-600 hover:text-gold-800">
                  Home
                </Link>
              </li>
              <li>
                <Link to="/design-quality-assurance" className="text-sm font-medium text-gray-600 hover:text-gray-900">
                  Evaluate Plan Set
                </Link>
              </li>
            </ul>
          </nav>
        </div>
      </header>

      <main className="flex-grow container mx-auto px-4 py-16">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-12">
            <h1 className="text-4xl font-bold mb-4">Evaluate Your Plan Set</h1>
            <p className="text-xl text-gray-600 mb-8">
              Upload your Plan Set PDFs for instant feedback and professional evaluation
            </p>
            <div className="flex justify-center">
              <Link to="/design-quality-assurance">
                <Button className="bg-gold-500 hover:bg-gold-600 text-white text-lg py-6 px-8">
                  Start Evaluation
                </Button>
              </Link>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mt-16">
            <div className="bg-white p-6 rounded-lg shadow-md text-center">
              <div className="h-12 w-12 rounded-full bg-gold-100 flex items-center justify-center mx-auto mb-4">
                <Upload className="h-6 w-6 text-gold-600" />
              </div>
              <h3 className="text-lg font-semibold mb-2">Upload Design</h3>
              <p className="text-gray-600">
                Simply upload your Plan Set PDF design files through our secure platform
              </p>
            </div>
            
            <div className="bg-white p-6 rounded-lg shadow-md text-center">
              <div className="h-12 w-12 rounded-full bg-gold-100 flex items-center justify-center mx-auto mb-4">
                <BarChart className="h-6 w-6 text-gold-600" />
              </div>
              <h3 className="text-lg font-semibold mb-2">Analyze Results</h3>
              <p className="text-gray-600">
                Our system evaluates your design across multiple quality criteria
              </p>
            </div>
            
            <div className="bg-white p-6 rounded-lg shadow-md text-center">
              <div className="h-12 w-12 rounded-full bg-gold-100 flex items-center justify-center mx-auto mb-4">
                <FileCheck className="h-6 w-6 text-gold-600" />
              </div>
              <h3 className="text-lg font-semibold mb-2">Get Feedback</h3>
              <p className="text-gray-600">
                Receive detailed feedback and suggestions for fixing issues
              </p>
            </div>
          </div>
        </div>
      </main>

      <footer className="bg-white border-t border-gray-200 py-6">
        <div className="container mx-auto px-4 text-center text-sm text-gray-500">
          © {new Date().getFullYear()} Design Quality Assurance. All rights reserved.
        </div>
      </footer>
    </div>
  );
};

export default Index;
