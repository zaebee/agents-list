import React, { useState, useEffect } from 'react';
import { CreditCard, DollarSign, Calendar, Download, AlertTriangle, CheckCircle, Users, TrendingUp } from 'lucide-react';
import { apiService } from '../services/api';
import { toast } from 'react-toastify';

interface SubscriptionInfo {
  subscription_id: string;
  tier: string;
  status: string;
  current_period_start: string;
  current_period_end: string;
  next_billing_date: string;
  amount: number;
  currency: string;
}

interface UsageInfo {
  user_id: string;
  subscription_tier: string;
  current_usage: {
    tasks_this_month: number;
    tasks_limit: number;
  };
  limits: {
    within_limits: boolean;
    warnings: any[];
    limits_exceeded: any[];
  };
  billing_summary: any;
  recommendations: any[];
}

interface PricingPlan {
  tier: string;
  name: string;
  pricing: {
    monthly: number;
    annual: number;
    annual_savings: number;
  };
  limits: {
    max_tasks_per_month: number | null;
    total_agents: number;
  };
  agent_breakdown: {
    haiku_agents: number;
    sonnet_agents: number;
    opus_agents: number;
  };
  features: string[];
  target_audience: string;
  support_level: string;
}

const BillingDashboard: React.FC = () => {
  const [subscription, setSubscription] = useState<SubscriptionInfo | null>(null);
  const [usage, setUsage] = useState<UsageInfo | null>(null);
  const [pricing, setPricing] = useState<{ pricing_plans: PricingPlan[] } | null>(null);
  const [invoices, setInvoices] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [upgradeModalOpen, setUpgradeModalOpen] = useState(false);

  useEffect(() => {
    loadBillingData();
  }, []);

  const loadBillingData = async () => {
    try {
      setLoading(true);
      const [subData, usageData, pricingData, invoicesData] = await Promise.all([
        apiService.getBillingInfo(),
        apiService.getUsageInfo(),
        apiService.getPricing(),
        apiService.getInvoices(),
      ]);
      
      setSubscription(subData);
      setUsage(usageData);
      setPricing(pricingData);
      setInvoices(invoicesData.invoices || []);
    } catch (error) {
      console.error('Failed to load billing data:', error);
      toast.error('Failed to load billing information');
      // Set mock data for demo
      setMockData();
    } finally {
      setLoading(false);
    }
  };

  const setMockData = () => {
    setSubscription({
      subscription_id: 'sub_demo123',
      tier: 'pro',
      status: 'active',
      current_period_start: new Date().toISOString(),
      current_period_end: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(),
      next_billing_date: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(),
      amount: 49.00,
      currency: 'USD',
    });

    setUsage({
      user_id: 'demo_user',
      subscription_tier: 'pro',
      current_usage: {
        tasks_this_month: 342,
        tasks_limit: 10,
      },
      limits: {
        within_limits: true,
        warnings: [],
        limits_exceeded: [],
      },
      billing_summary: {
        costs: {
          base_subscription: 49.00,
          additional_usage: 0,
          total: 49.00,
        },
        usage_summary: {
          tasks_completed: 342,
          tokens_consumed: 1250000,
          most_used_agents: [
            ['Code Reviewer', 89],
            ['Data Analyst', 67],
            ['Business Analyst', 54],
            ['Frontend Developer', 43],
            ['Security Auditor', 32],
          ],
        },
      },
      recommendations: [],
    });

    setPricing({
      pricing_plans: [
        {
          tier: 'free',
          name: 'Free Tier',
          pricing: { monthly: 0, annual: 0, annual_savings: 0 },
          limits: { max_tasks_per_month: 10, total_agents: 9 },
          agent_breakdown: { haiku_agents: 9, sonnet_agents: 0, opus_agents: 0 },
          features: ['9 Haiku agents', '10 tasks/month', 'Community support'],
          target_audience: 'Individual developers',
          support_level: 'community',
        },
        {
          tier: 'pro',
          name: 'Pro Tier',
          pricing: { monthly: 49, annual: 490, annual_savings: 98 },
          limits: { max_tasks_per_month: null, total_agents: 46 },
          agent_breakdown: { haiku_agents: 9, sonnet_agents: 37, opus_agents: 0 },
          features: ['46 total agents', 'Unlimited tasks', 'API access', 'Priority support'],
          target_audience: 'Startups and SMBs',
          support_level: 'email',
        },
        {
          tier: 'enterprise',
          name: 'Enterprise Tier',
          pricing: { monthly: 299, annual: 2990, annual_savings: 598 },
          limits: { max_tasks_per_month: null, total_agents: 59 },
          agent_breakdown: { haiku_agents: 9, sonnet_agents: 37, opus_agents: 13 },
          features: ['All 59 agents', 'Custom training', 'Dedicated support', 'SSO'],
          target_audience: 'Large enterprises',
          support_level: 'dedicated',
        },
      ],
    });

    setInvoices([
      {
        id: 'inv_demo1',
        number: 'INV-2024-001',
        amount_paid: 49.00,
        currency: 'USD',
        status: 'paid',
        created: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000),
        period_start: new Date(Date.now() - 60 * 24 * 60 * 60 * 1000),
        period_end: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000),
        hosted_invoice_url: 'https://example.com/invoice/demo1',
      },
      {
        id: 'inv_demo2',
        number: 'INV-2024-002',
        amount_paid: 49.00,
        currency: 'USD',
        status: 'paid',
        created: new Date(Date.now() - 60 * 24 * 60 * 60 * 1000),
        period_start: new Date(Date.now() - 90 * 24 * 60 * 60 * 1000),
        period_end: new Date(Date.now() - 60 * 24 * 60 * 60 * 1000),
        hosted_invoice_url: 'https://example.com/invoice/demo2',
      },
    ]);
  };

  const handleUpgrade = async (targetTier: string) => {
    try {
      await apiService.createSubscription({ tier: targetTier });
      toast.success('Subscription upgraded successfully!');
      setUpgradeModalOpen(false);
      loadBillingData();
    } catch (error) {
      toast.error('Failed to upgrade subscription');
    }
  };

  const handleCancelSubscription = async () => {
    if (!confirm('Are you sure you want to cancel your subscription?')) {
      return;
    }

    try {
      await apiService.cancelSubscription();
      toast.success('Subscription canceled successfully');
      loadBillingData();
    } catch (error) {
      toast.error('Failed to cancel subscription');
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  const formatCurrency = (amount: number, currency = 'USD') => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency,
    }).format(amount);
  };

  const getUsagePercentage = () => {
    if (!usage || !usage.current_usage.tasks_limit) return 0;
    return (usage.current_usage.tasks_this_month / usage.current_usage.tasks_limit) * 100;
  };

  const getTierColor = (tier: string) => {
    switch (tier) {
      case 'free': return 'bg-gray-100 text-gray-800';
      case 'pro': return 'bg-blue-100 text-blue-800';
      case 'enterprise': return 'bg-purple-100 text-purple-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Billing & Subscription</h1>
          <p className="text-gray-600">Manage your subscription, view usage, and billing history</p>
        </div>
        
        <div className="flex items-center space-x-4 mt-4 sm:mt-0">
          <button
            onClick={() => setUpgradeModalOpen(true)}
            className="btn-primary flex items-center space-x-2"
          >
            <TrendingUp className="h-4 w-4" />
            <span>Upgrade Plan</span>
          </button>
        </div>
      </div>

      {/* Usage Warnings */}
      {usage && usage.limits && usage.limits.warnings?.length > 0 && (
        // {usage?.limits?.warnings?.length > 0 && ( */
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 flex items-center space-x-3">
          <AlertTriangle className="h-5 w-5 text-yellow-600" />
          <div>
            <p className="text-yellow-800 font-medium">Usage Warning</p>
            <p className="text-yellow-700 text-sm">
              You're approaching your monthly limits. Consider upgrading to avoid service interruption.
            </p>
          </div>
        </div>
      )}

      {/* Current Subscription */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold">Current Subscription</h3>
            {subscription && (
              <span className={`inline-flex px-2 py-1 text-sm font-medium rounded-full ${getTierColor(subscription.tier)}`}>
                {subscription.tier.charAt(0).toUpperCase() + subscription.tier.slice(1)} Plan
              </span>
            )}
          </div>

          {subscription && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-gray-600">Status</span>
                <div className="flex items-center space-x-2">
                  <CheckCircle className="h-4 w-4 text-green-600" />
                  <span className="text-green-600 font-medium capitalize">{subscription.status}</span>
                </div>
              </div>

              <div className="flex items-center justify-between">
                <span className="text-gray-600">Monthly Cost</span>
                <span className="text-lg font-semibold">
                  {formatCurrency(subscription.amount, subscription.currency)}
                </span>
              </div>

              <div className="flex items-center justify-between">
                <span className="text-gray-600">Next Billing</span>
                <span className="font-medium">{formatDate(subscription.next_billing_date)}</span>
              </div>

              <div className="flex items-center justify-between">
                <span className="text-gray-600">Current Period</span>
                <span className="text-sm">
                  {formatDate(subscription.current_period_start)} - {formatDate(subscription.current_period_end)}
                </span>
              </div>

              <div className="pt-4 border-t border-gray-200">
                <button
                  onClick={handleCancelSubscription}
                  className="text-red-600 hover:text-red-700 text-sm font-medium"
                >
                  Cancel Subscription
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Usage Stats */}
        <div className="card p-6">
          <h3 className="text-lg font-semibold mb-4">Usage This Month</h3>
          
          {usage && (
            <div className="space-y-4">
              <div>
                <div className="flex justify-between items-center mb-2">
                  <span className="text-gray-600">Tasks Completed</span>
                  <span className="font-semibold">
                    {usage.current_usage.tasks_this_month.toLocaleString()}
                    {usage.current_usage.tasks_limit && ` / ${usage.current_usage.tasks_limit.toLocaleString()}`}
                  </span>
                </div>
                
                {usage.current_usage.tasks_limit && (
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-primary-600 h-2 rounded-full" 
                      style={{ width: `${Math.min(getUsagePercentage(), 100)}%` }}
                    ></div>
                  </div>
                )}
              </div>

              <div className="flex items-center justify-between">
                <span className="text-gray-600">Tokens Used</span>
                <span className="font-medium">
                  {usage.billing_summary.usage_summary.tokens_consumed.toLocaleString()}
                </span>
              </div>

              <div className="flex items-center justify-between">
                <span className="text-gray-600">Total Cost</span>
                <span className="text-lg font-semibold">
                  {formatCurrency(usage.billing_summary.costs.total)}
                </span>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Most Used Agents */}
      {usage?.billing_summary.usage_summary.most_used_agents && (
        <div className="card p-6">
          <h3 className="text-lg font-semibold mb-4">Most Used Agents</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
          </div>
        </div>
      )}

      {/* Billing History */}
      <div className="card overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <h3 className="text-lg font-semibold">Billing History</h3>
          <button className="text-primary-600 hover:text-primary-700 text-sm font-medium flex items-center space-x-1">
            <Download className="h-4 w-4" />
            <span>Export All</span>
          </button>
        </div>
        
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Invoice</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Period</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Amount</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {invoices.map((invoice) => (
                <tr key={invoice.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap font-medium text-gray-900">
                    {invoice.number}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-gray-600">
                    {formatDate(invoice.created)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-gray-600 text-sm">
                    {formatDate(invoice.period_start)} - {formatDate(invoice.period_end)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap font-medium">
                    {formatCurrency(invoice.amount_paid, invoice.currency)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="inline-flex px-2 py-1 text-xs font-medium rounded-full bg-green-100 text-green-800">
                      {invoice.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <a
                      href={invoice.hosted_invoice_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-primary-600 hover:text-primary-700 text-sm font-medium flex items-center space-x-1"
                    >
                      <Download className="h-4 w-4" />
                      <span>Download</span>
                    </a>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Upgrade Modal */}
      {upgradeModalOpen && pricing && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-4xl w-full mx-4 max-h-screen overflow-y-auto">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-bold">Choose Your Plan</h2>
              <button
                onClick={() => setUpgradeModalOpen(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                ×
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {pricing.pricing_plans.map((plan) => (
                <div
                  key={plan.tier}
                  className={`border rounded-lg p-6 ${
                    plan.tier === subscription?.tier 
                      ? 'border-primary-500 bg-primary-50' 
                      : 'border-gray-200'
                  }`}
                >
                  <div className="text-center mb-4">
                    <h3 className="text-xl font-bold">{plan.name}</h3>
                    <div className="text-3xl font-bold mt-2">
                      {formatCurrency(plan.pricing.monthly)}
                      <span className="text-base text-gray-600">/month</span>
                    </div>
                    {plan.pricing.annual_savings > 0 && (
                      <p className="text-sm text-green-600 mt-1">
                        Save {formatCurrency(plan.pricing.annual_savings)}/year with annual billing
                      </p>
                    )}
                  </div>

                  <ul className="space-y-2 mb-6">
                    {plan.features.map((feature, index) => (
                      <li key={index} className="flex items-center text-sm">
                        <CheckCircle className="h-4 w-4 text-green-600 mr-2 flex-shrink-0" />
                        {feature}
                      </li>
                    ))}
                  </ul>

                  {plan.tier === subscription?.tier ? (
                    <div className="text-center py-2 text-primary-600 font-medium">
                      Current Plan
                    </div>
                  ) : (
                    <button
                      onClick={() => handleUpgrade(plan.tier)}
                      className="w-full btn-primary"
                    >
                      {plan.tier === 'free' ? 'Downgrade' : 'Upgrade'} to {plan.name}
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default BillingDashboard;
