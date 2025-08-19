import React from 'react';
import Layout from '../components/layout/Layout';
import PortfolioTable from '../components/portfolio/PortfolioTable';

const DashboardPage: React.FC = () => {
  return (
    <Layout>
      <PortfolioTable />
    </Layout>
  );
};

export default DashboardPage;