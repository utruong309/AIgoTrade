import React, { useState } from 'react';
import {
  Box,
  TextField,
  Button,
  Typography,
  Alert,
  Paper,
  Container,
  MenuItem
} from '@mui/material';
import { authAPI } from '../../services/api';
import { useAuth } from '../../context/AuthContext';

const RegisterForm: React.FC = () => {
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    password_confirm: '',
    first_name: '',
    last_name: '',
    risk_tolerance: 'moderate',
    investment_experience: 'beginner',
    initial_cash: '10000'
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await authAPI.register(formData);
      if (response.data.success) {
        login(response.data.user, response.data.token);
      }
    } catch (err: any) {
      setError(err.response?.data?.error || 'Registration failed');
    }

    setLoading(false);
  };

  return (
    <Container maxWidth="sm">
      <Paper elevation={3} sx={{ p: 4, mt: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom align="center">
          Create Account
        </Typography>
        
        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
        
        <Box component="form" onSubmit={handleSubmit}>
          <TextField
            id="register-username"
            fullWidth
            label="Username"
            name="username"
            value={formData.username}
            onChange={handleChange}
            margin="normal"
            required
            autoComplete="username"
            inputProps={{
              'aria-describedby': 'register-username-helper'
            }}
          />
          <TextField
            id="register-email"
            fullWidth
            label="Email"
            name="email"
            type="email"
            value={formData.email}
            onChange={handleChange}
            margin="normal"
            required
            autoComplete="email"
            inputProps={{
              'aria-describedby': 'register-email-helper'
            }}
          />
          <Box sx={{ display: 'flex', gap: 2 }}>
            <TextField
              id="register-first-name"
              fullWidth
              label="First Name"
              name="first_name"
              value={formData.first_name}
              onChange={handleChange}
              margin="normal"
              autoComplete="given-name"
              inputProps={{
                'aria-describedby': 'register-first-name-helper'
              }}
            />
            <TextField
              id="register-last-name"
              fullWidth
              label="Last Name"
              name="last_name"
              value={formData.last_name}
              onChange={handleChange}
              margin="normal"
              autoComplete="family-name"
              inputProps={{
                'aria-describedby': 'register-last-name-helper'
              }}
            />
          </Box>
          <TextField
            id="register-password"
            fullWidth
            label="Password"
            name="password"
            type="password"
            value={formData.password}
            onChange={handleChange}
            margin="normal"
            required
            autoComplete="new-password"
            inputProps={{
              'aria-describedby': 'register-password-helper'
            }}
          />
          <TextField
            id="register-password-confirm"
            fullWidth
            label="Confirm Password"
            name="password_confirm"
            type="password"
            value={formData.password_confirm}
            onChange={handleChange}
            margin="normal"
            required
            autoComplete="new-password"
            inputProps={{
              'aria-describedby': 'register-password-confirm-helper'
            }}
          />
          <TextField
            id="register-risk-tolerance"
            fullWidth
            select
            label="Risk Tolerance"
            name="risk_tolerance"
            value={formData.risk_tolerance}
            onChange={handleChange}
            margin="normal"
            autoComplete="off"
            inputProps={{
              'aria-describedby': 'register-risk-tolerance-helper'
            }}
          >
            <MenuItem value="conservative">Conservative</MenuItem>
            <MenuItem value="moderate">Moderate</MenuItem>
            <MenuItem value="aggressive">Aggressive</MenuItem>
          </TextField>
          <TextField
            id="register-investment-experience"
            fullWidth
            select
            label="Investment Experience"
            name="investment_experience"
            value={formData.investment_experience}
            onChange={handleChange}
            margin="normal"
            autoComplete="off"
            inputProps={{
              'aria-describedby': 'register-investment-experience-helper'
            }}
          >
            <MenuItem value="beginner">Beginner</MenuItem>
            <MenuItem value="intermediate">Intermediate</MenuItem>
            <MenuItem value="advanced">Advanced</MenuItem>
          </TextField>

          <TextField
            id="register-initial-cash"
            fullWidth
            label="Initial Cash Balance"
            name="initial_cash"
            type="number"
            value={formData.initial_cash}
            onChange={handleChange}
            margin="normal"
            helperText="Starting cash for your portfolio"
            autoComplete="off"
            InputProps={{
              startAdornment: <span>$</span>,
            }}
            inputProps={{
              'aria-describedby': 'register-initial-cash-helper'
            }}
          />
          
          <Button
            type="submit"
            fullWidth
            variant="contained"
            sx={{ mt: 3, mb: 2 }}
            disabled={loading}
          >
            {loading ? 'Creating Account...' : 'Create Account'}
          </Button>
        </Box>
      </Paper>
    </Container>
  );
};

export default RegisterForm;