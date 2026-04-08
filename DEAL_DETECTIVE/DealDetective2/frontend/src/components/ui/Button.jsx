import React from 'react';
import { motion } from 'framer-motion';
import './UiStyles.css';

const Button = ({ children, variant = 'primary', onClick, disabled, className = '', ...props }) => {
  return (
    <motion.button
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      className={`btn btn-${variant} ${className}`}
      onClick={onClick}
      disabled={disabled}
      {...props}
    >
      {children}
    </motion.button>
  );
};

export default Button;
