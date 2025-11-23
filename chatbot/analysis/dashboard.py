import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from database.advanced_analysis_queries import (
    get_price_trend_analysis,
    get_size_availability_heatmap,
    get_discount_analysis,
    get_color_popularity_impact,
    get_rare_finds_analysis,
    get_best_value_recommendations,
    get_category_price_analysis
)
from database.basic_analysis_queries import (
    get_basic_metrics,
    get_category_distribution,
    get_price_range_analysis,
    get_availability_analysis,
    get_top_collections
)

def render_basic_insights():
    st.header("📊 Basic Market Overview")

    # Key Metrics
    st.subheader("🔑 Key Metrics")
    metrics_df = get_basic_metrics()
    if not metrics_df.empty:
        metrics = metrics_df.iloc[0]
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Models", f"{metrics['total_models']:,}")
        col2.metric("Color Variants", f"{metrics['total_color_variants']:,}")
        col3.metric("Available Items", f"{metrics['total_available_items']:,}")
        col4.metric("Avg Price", f"${metrics['average_price']:.2f}")

    # Analysis 1: Category Distribution
    st.subheader("📈 Category Distribution")
    category_df = get_category_distribution()
    if not category_df.empty:
        col1, col2 = st.columns(2)
        with col1:
            fig = px.pie(category_df, values='model_count', names='category',
                        title='Models by Category (Top 9 + Others)')
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            fig = px.bar(category_df, x='category', y='color_variant_count',
                        title='Color Variants by Category')
            st.plotly_chart(fig, use_container_width=True)

    # Analysis 2: Price Range Analysis
    st.subheader("💰 Price Range Distribution")
    price_range_df = get_price_range_analysis()
    if not price_range_df.empty:
        fig = px.bar(price_range_df, x='price_range', y='product_count',
                    title='Products by Price Range',
                    color='avg_price_in_range')
        st.plotly_chart(fig, use_container_width=True)

    # Analysis 3: Availability Analysis
    st.subheader("📦 Stock Availability")
    availability_df = get_availability_analysis()
    if not availability_df.empty:
        # Filter to top categories only for better visualization
        top_categories = availability_df.nlargest(8, 'total_listings')
        fig = px.bar(top_categories, x='category', y='availability_percent',
                    title='Availability Percentage by Top Categories',
                    color='availability_percent')
        st.plotly_chart(fig, use_container_width=True)

    # Analysis 4: Top Collections (with meaningful metrics)
    st.subheader("🏆 Top Collections Analysis")
    collections_df = get_top_collections()
    if not collections_df.empty:
        # Filter out "Other Collections" from premium metrics
        meaningful_collections = collections_df[collections_df['collection'] != 'Other Collections']

        if not meaningful_collections.empty:
            col1, col2 = st.columns(2)
            with col1:
                fig = px.bar(meaningful_collections, x='collection', y='model_count',
                            title='Models per Collection')
                st.plotly_chart(fig, use_container_width=True)
            with col2:
                fig = px.bar(meaningful_collections, x='collection', y='avg_price',
                            title='Average Price by Collection')
                st.plotly_chart(fig, use_container_width=True)

            # Meaningful metrics excluding "Other"
            st.subheader("🎯 Collection Insights")
            if len(meaningful_collections) >= 2:
                highest_avg = meaningful_collections.loc[meaningful_collections['avg_price'].idxmax()]
                lowest_avg = meaningful_collections.loc[meaningful_collections['avg_price'].idxmin()]
                most_models = meaningful_collections.loc[meaningful_collections['model_count'].idxmax()]
                best_stock = meaningful_collections.loc[meaningful_collections['total_available'].idxmax()]

                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Premium Line", highest_avg['collection'], f"${highest_avg['avg_price']:.2f}")
                col2.metric("Most Affordable", lowest_avg['collection'], f"${lowest_avg['avg_price']:.2f}")
                col3.metric("Largest Variety", most_models['collection'], f"{most_models['model_count']} models")
                col4.metric("Best Stock", best_stock['collection'], f"{best_stock['total_available']} items")

def render_advanced_analysis_dashboard():
    st.header("🎯 Advanced Nike Shoe Insights")

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "💰 Collection Pricing",
        "📊 Size Analysis",
        "🎯 Discounts",
        "🎨 Color Impact",
        "💎 Rare Finds",
        "🏆 Best Value"
    ])

    with tab1:
        st.subheader("💰 Collection Price Analysis")
        price_df = get_price_trend_analysis()
        if not price_df.empty:
            # Analysis 1: Bar chart of average prices
            fig = px.bar(price_df, x='collection', y='avg_price',
                        title='Average Price by Collection',
                        color='avg_price',
                        hover_data=['min_price', 'max_price', 'total_listings'])
            st.plotly_chart(fig, use_container_width=True)

            # Analysis 2: Price range visualization
            fig_range = go.Figure()
            for _, row in price_df.iterrows():
                fig_range.add_trace(go.Bar(
                    name=row['collection'],
                    x=[row['collection']],
                    y=[row['avg_price']],
                    error_y=dict(
                        type='data',
                        array=[row['max_price'] - row['avg_price']],
                        arrayminus=[row['avg_price'] - row['min_price']]
                    )
                ))
            fig_range.update_layout(title='Price Range by Collection (Bars show average, lines show min-max range)')
            st.plotly_chart(fig_range, use_container_width=True)

            # Analysis 3: Collection value metrics
            st.subheader("📊 Collection Value Metrics")
            col1, col2, col3 = st.columns(3)
            highest_avg = price_df.loc[price_df['avg_price'].idxmax()]
            lowest_avg = price_df.loc[price_df['avg_price'].idxmin()]
            most_listings = price_df.loc[price_df['total_listings'].idxmax()]

            col1.metric("Most Expensive Collection", highest_avg['collection'], f"${highest_avg['avg_price']:.2f}")
            col2.metric("Most Affordable Collection", lowest_avg['collection'], f"${lowest_avg['avg_price']:.2f}")
            col3.metric("Largest Collection", most_listings['collection'], f"{most_listings['total_listings']} listings")

    with tab2:
        st.subheader("📊 Size Availability Analysis")
        size_df = get_size_availability_heatmap()
        if not size_df.empty:
            # Analysis 1: Heatmap
            pivot_df = size_df.pivot(index='model', columns='size', values='currently_available')
            fig = px.imshow(pivot_df,
                           title='Size Availability Heatmap<br><sub>Darker colors = more available sizes</sub>',
                           color_continuous_scale='Blues',
                           aspect='auto')
            st.plotly_chart(fig, use_container_width=True)

            # Analysis 2: Size distribution per model
            st.subheader("📏 Size Distribution per Model")
            model_sizes = size_df.groupby('model')['currently_available'].sum().reset_index()
            fig_sizes = px.bar(model_sizes, x='model', y='currently_available',
                             title='Total Available Sizes per Model')
            st.plotly_chart(fig_sizes, use_container_width=True)

            # Analysis 3: Rare sizes alert
            st.subheader("🔔 Limited Stock Alerts")
            rare_sizes = size_df[size_df['currently_available'] <= 2]
            if not rare_sizes.empty:
                for _, row in rare_sizes.nlargest(8, 'avg_price').iterrows():
                    st.warning(f"**{row['model']}** - Size {row['size']}: ${row['lowest_price_available']} (Only {row['currently_available']} available)")
            else:
                st.info("No critically low stock items found.")

    with tab3:
        st.subheader("🎯 Discount Analysis")
        discount_df = get_discount_analysis()
        if not discount_df.empty:
            # Analysis 1: Discount distribution
            st.write(f"🎉 Found {len(discount_df)} items on sale!")

            fig_discount = px.histogram(discount_df, x='discount_percent',
                                      title='Distribution of Discount Percentages',
                                      nbins=20)
            st.plotly_chart(fig_discount, use_container_width=True)

            # Analysis 2: Top discounts table
            st.subheader("🔥 Top Discounts")
            top_discounts = discount_df.head(15)
            for _, row in top_discounts.iterrows():
                with st.expander(f"🏷️ {row['name']} - {row['color_name']} (Size {row['size']}) - {row['discount_percent']}% OFF"):
                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("Current", f"${row['price']}")
                    col2.metric("Original", f"${row['original_price']}")
                    col3.metric("You Save", f"${row['original_price'] - row['price']:.2f}")
                    col4.metric("Discount", f"{row['discount_percent']}%")
                    st.write(f"**Category:** {row['category']}")

            # Analysis 3: Discounts by category
            st.subheader("📦 Discounts by Category")
            category_discounts = discount_df.groupby('category').agg({
                'discount_percent': 'mean',
                'price': 'count'
            }).reset_index()
            category_discounts.columns = ['Category', 'Average Discount %', 'Number of Items']

            fig_cat = px.bar(category_discounts, x='Category', y='Average Discount %',
                           title='Average Discount Percentage by Category')
            st.plotly_chart(fig_cat, use_container_width=True)

    with tab4:
        st.subheader("🎨 Color Analysis")
        color_df = get_color_popularity_impact()
        if not color_df.empty:
            # Analysis 1: Color price vs availability scatter
            fig = px.scatter(color_df, x='models_available', y='avg_price',
                            size='currently_available', color='total_variants',
                            hover_name='color_name',
                            title='Color Analysis: Availability vs Price',
                            labels={'models_available': 'Models Available', 'avg_price': 'Average Price'})
            st.plotly_chart(fig, use_container_width=True)

            # Analysis 2: Top premium colors
            st.subheader("💎 Premium Colors")
            premium_colors = color_df.nlargest(8, 'avg_price')
            for _, row in premium_colors.iterrows():
                col1, col2, col3 = st.columns([2,1,1])
                col1.write(f"**{row['color_name']}**")
                col2.write(f"${row['avg_price']:.2f}")
                col3.write(f"{row['models_available']} models")

            # Analysis 3: Most popular colors
            st.subheader("📈 Most Available Colors")
            popular_colors = color_df.nlargest(8, 'currently_available')
            fig_popular = px.bar(popular_colors, x='color_name', y='currently_available',
                               title='Colors with Highest Availability')
            st.plotly_chart(fig_popular, use_container_width=True)

    with tab5:
        st.subheader("💎 Rare Finds & Limited Editions")
        rare_df = get_rare_finds_analysis()
        if not rare_df.empty:
            st.success(f"🎯 Found {len(rare_df)} rare and limited items!")

            # Analysis 1: Rare items display
            for idx, (_, row) in enumerate(rare_df.iterrows()):
                with st.expander(f"🌟 {row['name']} - {row['color_name']}"):
                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("Avg Price", f"${row['avg_price']:.2f}")
                    col2.metric("Size Options", row['sizes_available'])
                    col3.metric("Available", row['total_available'])
                    col4.metric("Price Range", f"${row['lowest_price']}-${row['highest_price']}")

                    scarcity_score = (row['total_available'] / row['sizes_available']) if row['sizes_available'] > 0 else 0
                    if scarcity_score < 2:
                        st.error("🚨 Very Limited Stock!")
                    elif scarcity_score < 5:
                        st.warning("⚠️ Limited Availability")
                    else:
                        st.info("💡 Moderately Available")

            # Analysis 2: Rarity vs Price analysis
            st.subheader("📊 Rarity vs Price Relationship")
            fig_rare = px.scatter(rare_df, x='total_available', y='avg_price',
                                size='sizes_available', hover_name='name',
                                title='Does Rarity Drive Price?',
                                labels={'total_available': 'Available Items', 'avg_price': 'Average Price'})
            st.plotly_chart(fig_rare, use_container_width=True)
        else:
            st.info("No rare finds detected in current inventory. All items have good availability!")

    with tab6:
        st.subheader("🏆 Best Value Recommendations")
        value_df = get_best_value_recommendations()
        if not value_df.empty:
            st.success(f"💡 Found {len(value_df)} high-value recommendations!")

            # Analysis 1: Improved Streamlit cards with better styling
            st.subheader("🎯 Top Value Picks")

            # Add custom CSS for beautiful cards
            st.markdown("""
                <style>
                .value-card {
                    border: 1px solid #e0e0e0;
                    border-radius: 12px;
                    padding: 16px;
                    margin: 12px 0;
                    background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
                    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
                    transition: transform 0.2s ease, box-shadow 0.2s ease;
                }
                .value-card:hover {
                    transform: translateY(-2px);
                    box-shadow: 0 6px 16px rgba(0,0,0,0.15);
                }
                .card-header {
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 12px;
                    margin: -16px -16px 16px -16px;
                    border-radius: 12px 12px 0 0;
                }
                </style>
            """, unsafe_allow_html=True)

            for i in range(0, len(value_df), 3):
                cols = st.columns(3)
                for j, col in enumerate(cols):
                    if i + j < len(value_df):
                        row = value_df.iloc[i + j]

                        with col:
                            # Create a beautiful card
                            with st.container():
                                # Start the card
                                st.markdown(f"""
                                    <div class="value-card">
                                        <div class="card-header">
                                            <div style="text-align: center; font-weight: bold; font-size: 14px;">TOP PICK</div>
                                        </div>
                                """, unsafe_allow_html=True)

                                # Image with better styling
                                image_url = row['sample_image_url'] if pd.notna(row['sample_image_url']) and row['sample_image_url'] != '' else "https://static.nike.com/a/images/t_PDP_1728_v1/f_auto,q_auto:eco/b7d9211c-26e7-431a-ac24-b0540fb3c00f/air-force-1-07-mens-shoes-jBrhbr.png"
                                st.image(image_url, use_container_width=True)

                                # Product info with better spacing
                                st.markdown(f"<h4 style='margin: 12px 0 4px 0; color: #333;'>{row['name']}</h4>", unsafe_allow_html=True)
                                st.markdown(f"<p style='color: #666; margin: 0 0 16px 0; font-style: italic;'>{row['category']}</p>", unsafe_allow_html=True)

                                # Metrics in a clean grid
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.metric("🎨 Colors", row['color_options'])
                                    st.metric("💰 Price", f"${row['avg_price']:.2f}")
                                with col2:
                                    st.metric("📏 Sizes", row['size_options'])
                                    st.metric("📦 Stock", row['total_available'])

                                # Value score with visual rating
                                score = row['value_score']
                                # Create a visual progress bar for value score
                                progress_width = min(score * 10, 100)  # Scale the score for progress bar

                                if score > 0.7:
                                    st.markdown(f"""
                                        <div style='background: linear-gradient(45deg, #4CAF50, #8BC34A); padding: 10px; border-radius: 8px; text-align: center; margin: 12px 0;'>
                                            <strong style='color: white; font-size: 14px;'>Excellent Value: {score:.2f} ⭐⭐⭐</strong>
                                        </div>
                                    """, unsafe_allow_html=True)
                                elif score > 0.5:
                                    st.markdown(f"""
                                        <div style='background: linear-gradient(45deg, #FF9800, #FFC107); padding: 10px; border-radius: 8px; text-align: center; margin: 12px 0;'>
                                            <strong style='color: white; font-size: 14px;'>Good Value: {score:.2f} ⭐⭐</strong>
                                        </div>
                                    """, unsafe_allow_html=True)
                                else:
                                    st.markdown(f"""
                                        <div style='background: linear-gradient(45deg, #2196F3, #03A9F4); padding: 10px; border-radius: 8px; text-align: center; margin: 12px 0;'>
                                            <strong style='color: white; font-size: 14px;'>Fair Value: {score:.2f} ⭐</strong>
                                        </div>
                                    """, unsafe_allow_html=True)

                                # Close the card
                                st.markdown('</div>', unsafe_allow_html=True)

            # Rest of the analyses...
            st.subheader("📈 Value Score Analysis")
            fig_value = px.histogram(value_df, x='value_score',
                                   title='Distribution of Value Scores',
                                   nbins=10,
                                   color_discrete_sequence=['#667eea'])
            st.plotly_chart(fig_value, use_container_width=True)

            st.subheader("💹 Price vs Variety Analysis")
            fig_options = px.scatter(value_df, x='avg_price', y='color_options',
                                   size='size_options',
                                   color='value_score',
                                   hover_name='name',
                                   title='Best Value: Balancing Price and Variety',
                                   color_continuous_scale='Viridis')
            st.plotly_chart(fig_options, use_container_width=True)

def render_analysis_dashboard():
    st.sidebar.subheader("Analysis Depth")
    analysis_depth = st.sidebar.radio("Choose Analysis Type", ["Basic Insights", "Advanced Analytics"])

    if analysis_depth == "Basic Insights":
        render_basic_insights()
    else:
        render_advanced_analysis_dashboard()